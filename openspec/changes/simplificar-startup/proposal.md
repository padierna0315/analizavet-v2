# Proposal: Simplify Startup Process

## Intent

To enable a simpler startup process for single-user deployment by making Redis and Dramatiq dependencies conditional. Currently, the application requires Redis + Dramatiq worker + FastAPI all running, but the MLLP TCP feature (the only reason for Dramatiq) is not in production yet. The goal is to allow double-click `iniciar.sh` → app starts without requiring Redis unless MLLP_ENABLED=true.

## Scope

### In Scope
- Modify `iniciar.sh` to conditionally start Redis and Dramatiq based on MLLP_ENABLED flag
- Update `app/tasks/broker.py` to defer Redis connection until first use
- Add MLLP_ENABLED and LOGFIRE_ENABLED flags to `settings.toml`
- Modify `app/main.py` to conditionally start MLLP adapter and Logfire instrumentation
- Update `app/satellites/ozelle/mllp_server.py` and `app/satellites/fujifilm/adapter.py` to respect conditional startup

### Out of Scope
- Removing WeasyPrint
- Removing SQLite
- Removing Dramatiq code (it stays but starts conditionally)
- Making any functional changes to existing tools

## Capabilities

### New Capabilities
- `conditional-startup`: Enable/disable services based on feature flags
- `config-flags`: Configuration management for feature flags

### Modified Capabilities
- `app-startup`: Startup process now supports conditional service activation
- `logging`: Logging configuration becomes conditional based on flags

## Approach

Implement lazy broker initialization in `broker.py` to defer Redis connection until first use. Add MLLP_ENABLED and LOGFIRE_ENABLED flags in settings.toml (both defaulting to false). Modify `iniciar.sh` to skip Redis + Dramatiq blocks when MLLP_ENABLED=false. Update `app/main.py` to conditionally enable Logfire instrumentation and MLLP adapter startup based on configuration flags.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `iniciar.sh` | Modified | Conditional startup of Redis and Dramatiq |
| `app/tasks/broker.py` | Modified | Lazy initialization of Redis connection |
| `app/main.py` | Modified | Conditional Logfire instrumentation and MLLP adapter startup |
| `settings.toml` | Modified | Add MLLP_ENABLED and LOGFIRE_ENABLED flags |
| `app/satellites/ozelle/mllp_server.py` | Modified | Conditional MLLP server startup |
| `app/satellites/fujifilm/adapter.py` | Modified | Conditional adapter startup |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| MLLP functionality might not start when expected | Low | Test MLLP_ENABLED=true flag during development |
| Logfire instrumentation may not work when disabled | Low | Verify configuration flags work correctly |
| Redis connection errors if MLLP enabled without Redis | Medium | Clear error messaging and documentation |

## Rollback Plan

1. Revert changes to `iniciar.sh` to original version
2. Restore original `broker.py` implementation
3. Remove MLLP_ENABLED and LOGFIRE_ENABLED flags from `settings.toml`
4. Restore `app/main.py` to original configuration
5. Revert changes to MLLP server and adapter files

## Dependencies

- None

## Success Criteria

- [ ] App starts with only `iniciar.sh` execution without requiring Redis/Dramatiq
- [ ] MLLP functionality works when MLLP_ENABLED=true
- [ ] Logfire instrumentation works when LOGFIRE_ENABLED=true
- [ ] All existing functionality preserved when features are enabled