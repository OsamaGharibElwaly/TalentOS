from evals.run_evals import lint_docker, main


def test_golden_eval_exits_zero_with_reproducible_metrics(capsys: object) -> None:
    code = main()
    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert code == 0
    assert "schema_validity: 100.00% (4/4)" in output
    assert "citation_pass_rate: 96.88% (31/32)" in output
    assert "rank_order: PASS" in output
    assert "RESULT: PASS" in output


def test_docker_blueprint_lints_without_building() -> None:
    assert lint_docker() == []
