# Proposal: Conectar Cables Taller

## Intent

Fix critical PDF generation issue in taller (workshop) where the PDF button is not working, along with related medium severity issues affecting report quality. The main problem is that the PDF button on the dashboard does not have the correct result_id to generate reports, preventing users from generating patient reports. Additionally, there are missing image parameter translations and clinical standards that affect the quality of generated reports.

## Scope

### In Scope
- Fixing the broken PDF button in taller dashboard to correctly generate patient reports
- Adding missing image parameter codes to IMAGE_PARAMETER_TRANSLATION
- Adding missing clinical standards for parameters like NSH#, LYM#, BAS#, etc.
- Fixing parameter alias resolution for LYM# → LYMP# mapping

### Out of Scope
- Refactoring the entire taller module
- Changing the overall structure of the taller UI

## Capabilities

### New Capabilities
- `taller-pdf-generation`: Enable proper PDF generation from taller dashboard with correct result_id handling
- `image-parameter-translation`: Add missing image parameter codes to translation mapping
- `clinical-standards`: Add missing clinical standards for various parameters

### Modified Capabilities
- `taller-workspace`: Update workspace HTML generation to include correct result_id for PDF generation
- `image-parameter-processing`: Update image parameter processing to include missing codes

## Approach

1. Fix the PDF button in taller dashboard to correctly pass result_id to generate reports
2. Update the workspace HTML generation to include the correct result_id in the button
3. Add missing image parameter codes to IMAGE_PARAMETER_TRANSLATION
4. Add missing clinical standards for parameters like NSH#, LYM#, BAS#, etc.
5. Fix parameter alias resolution for LYM# → LYMP# mapping

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/templates/taller/dashboard.html` | Modified | Fix PDF button to pass correct result_id |
| `app/routers/taller.py` | Modified | Update workspace HTML generation to include correct result_id |
| `app/core/reports/service.py` | Modified | Add missing image parameter codes |
| `app/routers/reports.py` | Modified | Add missing clinical standards for various parameters |
| `app/core/taller/images.py` | Modified | Fix parameter alias resolution |
| `app/core/algorithms/registry.py` | Modified | Add missing clinical standards |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking existing functionality | Low | Thorough testing of PDF generation and clinical standards |
| Missing image parameter codes | Low | Comprehensive review of all image parameter codes |
| Incorrect parameter alias resolution | Low | Verify all parameter aliases are correctly resolved |

## Rollback Plan

Revert changes to templates and Python files if issues arise. Remove added clinical standards and image parameter codes if they cause problems.

## Dependencies

- Working database connection for taller module
- Access to existing reports service

## Success Criteria

- [ ] PDF button works correctly with accurate result_id
- [ ] All image parameter codes are properly translated
- [ ] Clinical standards are correctly applied to parameters
- [ ] Parameter aliases are properly resolved