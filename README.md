Henry Ding
henryding2026@u.northwestern.edu

To run, simply run automate_odds.py on terminal, or do python automate_odds.py.

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
