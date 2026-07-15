from pvfactory.cli import main


def test_doctor_ok(capsys):
    assert main(["doctor"]) == 0
    err = capsys.readouterr().err
    assert "ffmpeg" in err and "bundled font" in err


def test_produce_requires_topic_or_backlog(tiny_profile):
    assert main(["produce", "--profile", str(tiny_profile), "--offline"]) == 2


def test_unknown_run_id_is_config_error(tmp_path):
    assert main(["inspect", "--run", "nope", "--output-root", str(tmp_path)]) == 2
