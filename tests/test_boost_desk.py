import pytest

import boost_desk
from boost_store import ranked_boosts

CLI_ADD = ["add", "--book", "fanduel", "--sport", "basketball_nba", "--event", "Celtics @ Lakers",
           "--market", "h2h", "--selection", "Boston Celtics", "--boost-pct", "50",
           "--max-stake", "50", "--type", "profit_boost"]


def test_add_then_rank(boost_env, fake_odds_api, capsys):
    assert boost_desk.main(CLI_ADD) == 0
    out = capsys.readouterr().out
    assert "Locked profit: $7.57" in out
    assert "Hedge: $119.93 on Los Angeles Lakers at FanDuel (1.48)" in out
    assert len(fake_odds_api) == 1

    saved = ranked_boosts()
    assert saved[0]["locked_profit"] == pytest.approx(7.57, abs=0.005)
    assert saved[0]["placed"] is False

    assert boost_desk.main(["rank"]) == 0
    assert "$7.57" in capsys.readouterr().out


def test_add_bonus_bet_shows_conversion(boost_env, fake_odds_api, capsys):
    args = ["add", "--book", "betmgm", "--sport", "basketball_nba", "--event", "Celtics",
            "--selection", "Boston Celtics", "--max-stake", "100", "--type", "bonus_bet_stake_not_returned"]
    assert boost_desk.main(args) == 0
    assert "58.38% of face value" in capsys.readouterr().out


def test_add_spread_needs_point_prints_message(boost_env, fake_odds_api, capsys):
    args = CLI_ADD + ["--market", "spreads"]
    assert boost_desk.main(args) == 1
    assert "point" in capsys.readouterr().err


def test_missing_key_prints_message_not_traceback(boost_env, fake_odds_api, monkeypatch, capsys):
    monkeypatch.delenv("ODDS_API_KEY")
    assert boost_desk.main(CLI_ADD) == 1
    assert "ODDS_API_KEY is not set" in capsys.readouterr().err
    assert fake_odds_api == []
    assert ranked_boosts() == []


def test_rank_with_nothing_saved(boost_env, capsys):
    assert boost_desk.main(["rank"]) == 0
    assert "No open promos" in capsys.readouterr().out
