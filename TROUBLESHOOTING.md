# eLabFTW Troubleshooting Guide

## Issue: "An internal error occurred" when creating/editing experiments

### Problem Description

When attempting to create or edit experiments in eLabFTW v5.3.6, users encounter an internal error with the message:

```
An internal error occurred. This should never happen!
Please contact support with the following identifier: [error-id]
```

The eLabFTW interface appears to work normally for other operations (viewing teams, dashboard, etc.), but specifically fails when accessing the experiment edit page.

### Symptoms

- ✅ Login works correctly
- ✅ Dashboard loads successfully
- ✅ Team page displays properly
- ✅ Experiments can be created via API (returns 201)
- ❌ Opening experiment edit page fails with error 500
- ❌ Generic "internal error" message shown to user

### Root Cause

**Incomplete JSON permissions structure in the database.**

eLabFTW v5.3.6+ requires permissions fields (`default_read`, `default_write`, `canread`, `canwrite`) to include specific array keys: `teams`, `users`, and `teamgroups`.

**Incorrect format** (causes the error):
```json
{
  "base": 20,
  "book": false
}
```

**Correct format** (required by eLabFTW):
```json
{
  "base": 20,
  "book": false,
  "teams": [],
  "users": [],
  "teamgroups": []
}
```

### Technical Details

The error occurs in `PermissionsHelper.php` line 40 when eLabFTW's permission editor attempts to read the `teams` array from the JSON object. If this key doesn't exist, PHP returns `null`, which causes a `TypeError` when the code expects an array:

```
TypeError: Elabftw\Models\Teams::readNamesFromIds():
  Argument #1 ($idArr) must be of type array, null given
```

### When This Happens

This issue typically occurs when:

1. **Users are created via direct SQL insertion** (bypassing eLabFTW's normal user creation flow)
2. **Using simplified permission JSON** from older documentation or examples
3. **Migrating from older eLabFTW versions** where permission format was simpler

### Solution 1: Fix Existing Data (Immediate Fix)

If you already have users or experiments with incomplete permissions, run these SQL commands:

```bash
# Get MySQL password from the container
MYSQL_PASS=$(docker exec mysql sh -c 'echo $MYSQL_PASSWORD')

# Fix all user default permissions
docker exec mysql mysql -uelabftw -p${MYSQL_PASS} elabftw -e "
UPDATE users SET
  default_read = JSON_SET(default_read,
    '$.teams', JSON_ARRAY(),
    '$.users', JSON_ARRAY(),
    '$.teamgroups', JSON_ARRAY()
  ),
  default_write = JSON_SET(default_write,
    '$.teams', JSON_ARRAY(),
    '$.users', JSON_ARRAY(),
    '$.teamgroups', JSON_ARRAY()
  )
WHERE JSON_EXTRACT(default_read, '$.teams') IS NULL;
"

# Fix all experiment permissions
docker exec mysql mysql -uelabftw -p${MYSQL_PASS} elabftw -e "
UPDATE experiments SET
  canread = JSON_SET(canread,
    '$.teams', JSON_ARRAY(),
    '$.users', JSON_ARRAY(),
    '$.teamgroups', JSON_ARRAY()
  ),
  canwrite = JSON_SET(canwrite,
    '$.teams', JSON_ARRAY(),
    '$.users', JSON_ARRAY(),
    '$.teamgroups', JSON_ARRAY()
  )
WHERE JSON_EXTRACT(canread, '$.teams') IS NULL;
"
```

**PowerShell version:**
```powershell
# Get MySQL password
$MYSQL_PASS = docker exec mysql sh -c 'echo $MYSQL_PASSWORD'

# Fix user permissions
docker exec mysql mysql -uelabftw -p"$MYSQL_PASS" elabftw -e "UPDATE users SET default_read = JSON_SET(default_read, '`$.teams', JSON_ARRAY(), '`$.users', JSON_ARRAY(), '`$.teamgroups', JSON_ARRAY()), default_write = JSON_SET(default_write, '`$.teams', JSON_ARRAY(), '`$.users', JSON_ARRAY(), '`$.teamgroups', JSON_ARRAY()) WHERE JSON_EXTRACT(default_read, '`$.teams') IS NULL;"

# Fix experiment permissions
docker exec mysql mysql -uelabftw -p"$MYSQL_PASS" elabftw -e "UPDATE experiments SET canread = JSON_SET(canread, '`$.teams', JSON_ARRAY(), '`$.users', JSON_ARRAY(), '`$.teamgroups', JSON_ARRAY()), canwrite = JSON_SET(canwrite, '`$.teams', JSON_ARRAY(), '`$.users', JSON_ARRAY(), '`$.teamgroups', JSON_ARRAY()) WHERE JSON_EXTRACT(canread, '`$.teams') IS NULL;"
```

### Solution 2: Prevent Future Occurrences

If you create users via SQL (e.g., in deployment scripts), always use the complete permission format:

**Correct SQL for user creation:**
```sql
INSERT INTO users (
    email, password_hash, firstname, lastname,
    validated, is_sysadmin, lang, default_read, default_write
) VALUES (
    'admin@localhost',
    '[password_hash]',
    'Admin',
    'User',
    1,
    1,
    'en_GB',
    JSON_OBJECT(
        'base', 20,
        'book', false,
        'teams', JSON_ARRAY(),
        'users', JSON_ARRAY(),
        'teamgroups', JSON_ARRAY()
    ),
    JSON_OBJECT(
        'base', 20,
        'book', false,
        'teams', JSON_ARRAY(),
        'users', JSON_ARRAY(),
        'teamgroups', JSON_ARRAY()
    )
);
```

### Verification

After applying the fix, verify the permissions are correct:

```bash
# Check user permissions
docker exec mysql mysql -uelabftw -p${MYSQL_PASS} elabftw -e \
  "SELECT userid, email, default_read, default_write FROM users LIMIT 1;"

# Check experiment permissions
docker exec mysql mysql -uelabftw -p${MYSQL_PASS} elabftw -e \
  "SELECT id, canread, canwrite FROM experiments LIMIT 1;"
```

Expected output should show JSON objects with `teams`, `users`, and `teamgroups` arrays:
```json
{
  "base": 20,
  "book": false,
  "teams": [],
  "users": [],
  "teamgroups": []
}
```

### How to Debug This Issue

If you encounter this error in the future, here's how to diagnose it:

1. **Check the container logs** for the actual PHP error:
   ```bash
   docker compose logs --tail=100 web
   ```

2. **Look for TypeError or "Undefined array key"** messages mentioning `teams`, `PermissionsHelper.php`, or permission-related files.

3. **Inspect the database** to see the actual JSON structure:
   ```bash
   docker exec mysql mysql -uelabftw -p[password] elabftw -e \
     "SELECT canread FROM experiments WHERE id = [experiment_id];"
   ```

4. **Compare with expected format** - if `teams`, `users`, or `teamgroups` keys are missing, apply the fix.

### Files Modified in This Project

The following deployment scripts have been updated to use the correct permission format:

- **`deploy-local.py`** (lines 350-351): User creation with complete JSON permissions
- **`create_admin_user.py`** (lines 97-98): User creation with complete JSON permissions

### References

- **eLabFTW Permissions Documentation**: https://doc.elabftw.net/sysadmin-guide.html
- **eLabFTW GitHub Issues**: Permissions system discussions in issues #1999, #2050, #2304, #2581, #3925
- **Permission Format Structure**: `{"base": <level>, "teams": [], "users": [], "teamgroups": []}`

### Common Permission Base Values

- `10` = Private (owner only)
- `20` = Team (all team members can read)
- `30` = Organization (all users can read)
- `40` = Public (anyone can read)

### Additional Notes

- The `book` field is legacy and can be set to `false` for new installations
- Write permissions implicitly include read access
- Sysadmins can force visibility by updating permissions via SQL
- This issue affects **experiments**, **items**, and **templates** that use the same permission structure

---

## Other Common Issues

### Issue: SSL Certificate Warnings

**Problem**: Browser shows "Your connection is not private" when accessing https://localhost:3148

**Solution**: This is expected with self-signed certificates. Click "Advanced" → "Proceed to localhost" in your browser. For production, use proper SSL/TLS certificates with Let's Encrypt.

### Issue: Database Connection Failed

**Problem**: eLabFTW container can't connect to MySQL

**Solution**:
1. Ensure MySQL container is healthy: `docker compose ps`
2. Verify DB_PASSWORD matches in both containers
3. Check healthcheck passes: `docker inspect mysql --format='{{.State.Health.Status}}'`
4. Wait 1-2 minutes for MySQL initialization on first boot

### Issue: Permission Denied Errors in Logs

**Problem**: nginx bind() permission denied on CentOS/RHEL

**Solution**: Comment out the `cap_drop` and `cap_add` sections in docker-compose.yml for the web service (see lines 55-62).

---

## Need More Help?

- **eLabFTW Documentation**: https://doc.elabftw.net
- **GitHub Issues**: https://github.com/elabftw/elabftw/issues
- **Community Forum**: https://github.com/elabftw/elabftw/discussions
- **Local Deployment Docs**: See `DEPLOY-LOCAL.md` in this repository
