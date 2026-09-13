from hermes_core.compatibility import CompatibilityAnalyzer, UpstreamState

def test_dirty_or_conflicted_state_never_reports_compatible():
    r=CompatibilityAnalyzer().analyze(UpstreamState(clean=False),conflict_files=('x.py',))
    assert not r.compatible and 'x.py' in r.conflicts and 'human approval before apply' in r.actions
