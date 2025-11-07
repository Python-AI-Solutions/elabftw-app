# Issue Summary: eLabFTW "Internal Error" When Creating Experiments

**Date**: November 5, 2025
**eLabFTW Version**: 5.3.6
**Deployment**: Docker Compose (local development)

---

## The Problem

Creating or editing experiments in eLabFTW resulted in an internal error:

```
An internal error occurred. This should never happen!
Please contact support with the following identifier: d9ca980b-b372-4711-8fd2-a19e4de59118
```

## Root Cause

**Incomplete JSON permissions structure in database fields.**

When users were created via direct SQL insertion (in our `deploy-local.py` and `create_admin_user.py` scripts), the permission fields used a simplified format:

```json
{"base": 20, "book": false}
```

However, eLabFTW v5.3.6 requires these fields to include three additional empty arrays:

```json
{
  "base": 20,
  "book": false,
  "teams": [],
  "users": [],
  "teamgroups": []
}
```

When eLabFTW's `PermissionsHelper.php` tried to access the `teams` array (which didn't exist), PHP returned `null` instead of an array, causing a `TypeError` that crashed the experiment edit page.

## The Investigation Process

1. **Checked deployment** - Docker containers running, database properly configured
2. **Verified database** - User-team associations correct, experiment created successfully
3. **Examined logs** - Found PHP error: `Undefined array key "teams"` in `PermissionsHelper.php:40`
4. **Compared JSON structures** - Discovered missing `teams`, `users`, `teamgroups` arrays
5. **Researched eLabFTW docs** - Confirmed required permission format

## The Solution

### 1. Fixed Existing Data (Immediate)

Updated all users and experiments with the correct JSON structure:

```bash
# Fix user default permissions
docker exec mysql mysql -uelabftw -p[password] elabftw -e "
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
  );
"

# Fix experiment permissions
docker exec mysql mysql -uelabftw -p[password] elabftw -e "
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
  );
"
```

### 2. Updated Deployment Scripts (Prevention)

Modified `deploy-local.py` and `create_admin_user.py` to create users with the complete permission format:

**Before:**
```python
JSON_OBJECT('base', 20, 'book', false)
```

**After:**
```python
JSON_OBJECT(
    'base', 20,
    'book', false,
    'teams', JSON_ARRAY(),
    'users', JSON_ARRAY(),
    'teamgroups', JSON_ARRAY()
)
```

## Results

✅ Experiments can now be created and edited successfully
✅ Permission editor loads without errors
✅ Future deployments will create users with correct format
✅ Documented in `TROUBLESHOOTING.md` for future reference

## Key Takeaways

1. **Direct SQL user creation** requires careful attention to eLabFTW's expected JSON structure
2. **eLabFTW's permission system** requires `teams`, `users`, and `teamgroups` arrays even if empty
3. **Container logs are essential** - the actual PHP error was hidden behind a generic user-facing message
4. **Database inspection** confirmed the schema was correct but data format was incomplete

## Files Modified

- `deploy-local.py` (lines 350-351)
- `create_admin_user.py` (lines 97-98)
- `TROUBLESHOOTING.md` (created - comprehensive guide)

## For Future Reference

**Complete troubleshooting guide**: See `TROUBLESHOOTING.md`
**Quick fix command**: See "Solution 1" section above
**Prevention**: Always use complete JSON format when creating users via SQL

---

## Timeline

1. **Issue encountered**: Error when creating/editing experiments
2. **Initial investigation**: Verified deployment, database, logs
3. **Root cause identified**: Missing JSON array keys in permissions
4. **Fix applied**: Updated database with correct JSON structure
5. **Prevention implemented**: Updated deployment scripts
6. **Documentation created**: TROUBLESHOOTING.md and this summary

## Questions or Need Help?

See `TROUBLESHOOTING.md` for detailed diagnostic steps and additional common issues.
