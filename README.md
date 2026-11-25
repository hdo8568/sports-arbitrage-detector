
To run, simply run automate_odds.py on terminal, or do python automate_odds.py.

## Setup

Keys and passwords no longer live in the code. Copy `.env.example` to `.env` and fill in your
Odds API key (`ODDS_API_KEY`) and the alert email login (`EMAIL_USER`, `EMAIL_PASS`, `EMAIL_TO`).
`.env` is gitignored, so it never gets pushed. On EC2, put the `.env` in the project folder
(or export the same variables in the cron environment).

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env
```

## API

There's a small read-only FastAPI app over the database:

```
uvicorn api:app --reload
```

Then go to http://127.0.0.1:8000/docs. Endpoints:
- `GET /health`
- `GET /odds?sport=basketball_nba&limit=50` latest odds rows
- `GET /arbitrage?total_stake=100` stored arbitrage opportunities with suggested stakes
- `GET /kelly?odds=2.10&prob=0.52&bankroll=1000&fraction=0.25` Kelly bet size

## Kelly sizing

`kelly.py` does two things. First, for an arbitrage it splits your total stake across both
sides so you get paid the same no matter who wins (each alert email now shows these stakes,
$100 total by default, change it with `ARB_TOTAL_STAKE`). Second, for a single +EV bet it
uses the Kelly criterion: given the decimal odds and our fair win probability (from the no-vig
calculation), bet `(b*p - q) / b` of the bankroll, where `b` is odds minus 1. Full Kelly is
very swingy, so the default is quarter Kelly (`fraction=0.25`). If there's no edge, it says bet 0.

## Boost Desk

I've already used every NY welcome offer, so what's left is the daily stuff: profit boosts,
odds boosts and bonus bets. Boost Desk tells me what one is worth and how to hedge it.

Put the books I can bet at in `.env` (Odds API keys or names, any case):

```
BOOKS=draftkings,fanduel,betmgm,caesars,espnbet,fanatics,betrivers
```

Then add a promo:

```
python boost_desk.py add --book fanduel --sport basketball_nba --event "Celtics @ Lakers" \
    --selection "Boston Celtics" --boost-pct 50 --max-stake 50 --type profit_boost
```

It pulls the game's odds from The Odds API, takes the vig out of Pinnacle's line with the
power method (or averages every book that has the line if Pinnacle doesn't), and gives me the
EV, the best price on the other side at my books, the hedge stake and the profit I lock in.
Every promo goes into a `boosts` table in `boosts.db`, with `placed` and `actual_result` /
`actual_profit` columns so I can track what I actually kept.

Worked example: FanDuel gives me a 50% profit boost on the Celtics at 2.70 (+170), max $50.
The profit on $1 goes from 1.70 to 2.55, so the boosted odds are 3.55. The best Lakers price
at my books is 1.48 (-208) at FanDuel. Hedge stake is 50 x 3.55 / 1.48 = $119.93 on the Lakers.
If the Celtics win I get 177.50 back, minus the 50 and the 119.93, so $7.57. If the Lakers win
I get 119.93 x 1.48 = 177.50 back, minus the same 169.93, so $7.57 again. Same money either way.

```
python boost_desk.py rank
```

shows today's promos I haven't placed yet, most locked profit first, then EV.

Promo types: `profit_boost`, `odds_boost` (give `--boosted-odds` instead of `--boost-pct`) and
`bonus_bet_stake_not_returned` (no odds needed, it uses the book's price, and it also shows the
conversion as a percent of the bonus). For spreads and totals add `--market spreads` or
`--market totals` and the line with `--point`.

It warns me when there's no other side to hedge (like a soccer three-way), when the hedge price
is too short and I'd lose money, when my stake is over the promo max, or when `BOOKS` isn't set.
Each `add` costs one Odds API credit per region (5 by default, since Pinnacle is in eu); set
`ODDS_REGIONS` to spend less. It doesn't place bets or log into anything, I still do that myself.

## Tests

```
pytest
```

Tests use a temporary SQLite file and never call the Odds API or send email.
`test_odds_api.py` in the root is still the manual script that hits the real API.

## About

This project is just a sports arbitrage detector. I use OddsAPI which collects data
from all sportsbooks. I collect all datra for NBA moneyline/head2head games and find
the best odds for both sides. This project also gives functionality for figuring out
vig, true odds, and implied probability. After we find the "best" odds for both sides,
we see if there exists an arbitrage opportunity between them. If so, then it is appended
to our SQL database, whose information we send back to us via email. Of course, I used a completely
separate email, specifically for arbitrage notifications, due to the sheer amount of emails being received. 
I connected to an EC2 on Amazon Web Services. With this, I was able to run automate_odds.py every 
10 minutes. Essentially, we collect data and put in arbitrage opportunities to a database every 10 minutes, then 
email the list of arbitrage opporunities. Hence, we can get an email every ten minutes, which required this new email.

This project is being actively expanded. The greatest pitfall is our use of OddsAPI. We aren't abe to then collect odds quickly and in
real time, since OddsAPI can be delayed often. The plan is to scrape data dierectly from our sportsbooks, such as Draftkings, Fanduel, etc..
This not only saves us money in subscription fees to OddsAPI but allows use to get real-time arbitrage opportunities. Furthermore, this project
is looking to expand out of moneyline/head2head games. We next look to player props (Steph Curry > 25.5 points). Instead of arbitrage opportunities,
we look to postiive expected value (+EV) bets. The proposition is that we collect data from all sports books. We then create a function to determine
our perceived true odds. This function is as follows. We first find the "best" sportsbooks, often those that are the largest and have devoted most
time to research and optimizing lines, such as Draftkings and Fanduel, among others. We produce a "weighting" function that provides some weight for each 
sportsbook. Those sportsbooks with most variance in their propositions receive less weighting. Then, we use our existing code to discern the implied 
probability. For every book whose odds are better than our implied probability, we have determined a positive expected value bet. We then can turn these
into parlays. 
