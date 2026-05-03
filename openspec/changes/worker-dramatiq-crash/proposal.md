# Proposal: Fix Dramatiq Worker Crash

## Intent

The Dramatiq worker crashes when starting because the Prometheus middleware attempts to bind to a port (9191/9200) that may already be in use from a previous worker that didn't clean up properly. This causes the new worker to fail to start because the port is already bound.

## Scope

### In Scope
- Fix the misleading comment in `app/tasks/broker.py` that claims "Prometheus middleware is disabled" when it's actually enabled by default
- Implement a solution to prevent port conflicts when starting new Dramatiq workers
- Update the worker startup script to handle Prometheus middleware configuration properly

### Out of Scope
- Changing the Dramatiq version
- Modifying Redis configuration
- Changing the core Dramatiq worker functionality

## Capabilities

### New Capabilities
- `dramatiq-worker-management`: Managing Dramatiq worker startup and configuration to prevent port conflicts

### Modified Capabilities
- `background-jobs`: Update to handle worker startup with proper middleware configuration

## Approach

The approach involves configuring the Dramatiq worker to prevent the Prometheus middleware from causing port conflicts. This can be achieved through one of three methods:
1. Configure the worker startup script to kill any existing Dramatiq processes before starting new workers
2. Configure Dramatiq to not include Prometheus middleware by default
3. Configure a different Prometheus port via environment variables

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/tasks/broker.py` | Modified | Update misleading comment and configure middleware properly |
| `iniciar.sh` | Modified | Update worker startup command to handle port conflicts |
| `requirements.txt` | None | No change to Dramatiq version or dependencies |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Incorrect middleware configuration | Low | Test thoroughly with different scenarios |
| Process cleanup failure | Low | Implement proper process management in iniciar.sh |

## Rollback Plan

If the changes cause issues, we can rollback by:
1. Reverting the changes to `iniciar.sh` and `app/tasks/broker.py`
2. Restoring the previous behavior where the port conflict issue will reappear

## Dependencies

- Dramatiq 1.15.0 with Redis
- uv for package management
- Redis server for message queuing

## Success Criteria

- [ ] Dramatiq workers start without port conflict errors
- [ ] Prometheus middleware is properly configured
- [ ] The misleading comment in broker.py is corrected
- [ ] Worker startup script handles process cleanup properly