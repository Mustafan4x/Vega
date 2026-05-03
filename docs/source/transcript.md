# Source video transcript

This file is the source material for SPEC.md. It is the transcript of a YouTube video that recommended building a Black Scholes options pricer as a quant interview pet project. It has been lightly reformatted for readability and split into section headers; the spoken content is preserved verbatim within each section.

## Source

* **URL**: https://www.youtube.com/watch?v=lY-NP4X455U
* **Speaker**: anonymous quant trading practitioner, advising candidates on portfolio projects
* **Coverage**: this transcript covers content from approximately the 1:40 mark to the end of the video
* **Provided by**: Mustafa, on 2026-05-02

## Key points (TL;DR for future Claude sessions)

The speaker outlines an incremental build path that levels up the project at each step. Read this if you only need the gist; read the full transcript below for nuance.

1. **Build a Black Scholes pricer in Python.** The five inputs are: volatility, stock price, strike price, time to expiry, and risk free interest rate. Output: a call price and a put price.
2. **Start with a REPL.** A simple Python repl-style application that takes the five inputs and prints both call and put values.
3. **Add a GUI with Streamlit.** Inputs on the left, "Calculate" button, output: call and put values.
4. **Add a heat map visualization.** Shock the two most sensitive inputs (volatility and stock price) and display the call and put values across the resulting grid. Make values configurable.
5. **Use green and red coloring properly.** Greener for higher numbers, redder for lower. The coloring becomes far more meaningful when paired with the next step.
6. **Allow user to enter a purchase price for the call and the put.** Now the heat map can show P&L instead of value: green for positive P&L, red for negative.
7. **Persist data to a relational database.** Demonstrates ability to wrangle data, which is core to a quant trading job.
   * Two tables: `inputs` and `outputs`, linked by a `calculation_id`.
   * `inputs` table: 6 columns (price, strike, time to expiry, volatility, interest rate, calculation_id).
   * `outputs` table: 4 columns (vol shock, stock price shock, call value, calculation_id), with multiple rows per `calculation_id` (one per heat map cell). Optionally a 5th column as a unique identifier for the (vol, stock) shock combination.
8. **Books referenced**: Sheldon Natenberg, *Option Volatility and Pricing*. Other Python data analysis books are linked in the video's description box (not included here).

## Full transcript (lightly reformatted)

### On choosing the project: Black Scholes

I usually recommend people to start with that shows passion that shows dedication is building a Black Scholes option pricer. Now if you read *Option Volatility and Pricing* by Sheldon Natenberg you'll know that there's a lot of different ways to price an option. There's the binomial pricing model for example, there's the Black Scholes pricing model, there are other pricing models that change certain assumptions and relax certain restrictions, but the number one way that you are going to be understanding option pricing theory is through the Black Scholes option model.

### Step 1: Python REPL

Let's take a look at this person's pet project. I recommend that this person builds a Black Scholes option pricer and I recommend that they start off small. I recommend that they start off with a Python repl application that literally takes in the five inputs to an options price (volatility, a stock price, strike price, time to expiry, and interest rate) and spits out both a call and a put value.

### Step 2: GUI with Streamlit

The next step to kind of level up your skills and really create something that you're proud of that you can put on a resume is to now add a kind of like a GUI layer, an interactive GUI layer, and the best way to do so is via a library called Streamlit, and that's exactly what this person did. So if you look at what he did on the left hand side you have a couple of the inputs that are required for the options price (current asset price, strike price, time to maturity, volatility, risk free interest rate, etc). Once you hit calculate it spits out both a call and a put price given these inputs.

### Step 3: Heat map visualization

All right, now if you want to take things a step further, because this is still a little simple, it's nice but it's not really something to brag about per se in an interview, you can then take that and now visualize that. Visualize that by shocking the most sensitive inputs to an options price (that being volatility and the actual stock price itself) and generating a heat map that displays the call and the put values at various different volatilities and various different stock prices.

Now what this individual decided to do is they also decided to make those values configurable, which is once again taking it a step higher. As we progress throughout this video guys you're really going to see a roadmap as to how you build something from a Python repl application to adding layers of complexity to make this something that gives you more bragging rights and is more impressive to both the interviewer and the employer.

### Step 4: Green and red coloring, plus P&L mode

Okay now what this person did that he could have done a bit better is he could have actually made the values in the heat map green and red, in the sense that greener values reflect higher numbers, redder values reflect lower numbers. But where this would have really really made sense would be if, taking this project a step further, this person decided to allow the user to input a purchase price for the call and a purchase price for the put. So pay close attention if you're thinking of doing a project like this, which I do recommend: input a purchase price for the call (or rather, allow the user to) for the call and the put. You will then have a P&L for the call and the put given your inputs and given the purchase price. Then the heat map, instead of displaying just the value of the call, can now represent the actual P&L of the call and the put given the inputs and the purchase price. And that's when green and red make a lot more sense: green is for positive P&L, red is for negative P&L.

Okay, hopefully you guys are following along and this is clear so far with also the visuals that I'm putting on screen for you guys.

### Step 5: Database persistence

Now as a quantitative trader another component of your job is going to be interacting with a bunch of data and consuming that data. Now I already recommended a couple of books for Python data analysis which will be linked in the description box below, but you also want to show the employer that you can actually mangle with, wrangle with, wrestle with (whatever word you want to use to represent your ability to proficiently consume data).

Now what will usually happen in a quantitative trading firm is you might have like a data, like a repository of data, that quant researchers and quant traders will query in order to back test certain strategies, develop certain frameworks, and just in general test certain ideas.

How do you involve the ability for a quantitative trader to use data efficiently with your pet project? What you might want to do for example is every time somebody clicks calculate, you save both the inputs and the outputs into a MySQL relational database. Use any relational database you want, that's not the point of this video. The point is that you are mapping inputs to outputs.

What's an idea, how would you do that? Well, as a software engineer an idea that I might have for example would be to save the base inputs into a table called the `inputs` table for example. That `inputs` table might have for example six columns: the five base inputs (price, strike, time to expiry, volatility, interest rate) and a sixth column that is the `calculation_id`.

For example the `output` table is going to have all the values in the heat map, so it'll have multiple rows for every distinct set of inputs and it'll have a couple of columns. The first two columns will be the vol and the future shock, or the vol and the stock price shock (right, the change in the actual stock price against the base input which for example in the base case might be zero on the vol and zero on the actual stock itself). You might have plus one on the vol and zero on the stock, minus two on the stock and plus one on the vol, etc.

The third column is going to be the P&L associated with that given shock and input, or it just might be the call's value (in fact I think should probably stick to the call value for now for simplicity).

Okay the fourth column is going to be the `calculation_id` that'll link that output to a distinct set of inputs in the `inputs` table. So once again: two tables, six columns in the first table, four columns in the second table. You can actually maybe even add a fifth column to the second table that is the unique identifier for a given shock to vol and future combination. That becomes a little more involved but at the same time it just goes to show that you're able to think about data and structure data in a cohesive and cogent manner.

### Conclusion (not directly relevant to the build, kept for context)

Hopefully this video was able to help you guys understand the sort of pet project that employers are looking for. Guys if you'd like to better understand the world of quantitative trading I do resume reviews, technical interviews, behavioral interviews for quant devs, quant traders, etc. You can do so by speaking to me one on one (Calendly link in the description box below). If you'd like to watch this video up to a week early guys, Patreon link in the description box below; you also gain access to my exclusive Discord. And if you would like to stalk me behind the scenes to see what I'm doing in real life, I post almost nothing quant related on my Instagram, but if you'd like to follow me on Instagram you can go ahead and do so (link in the description box below). Guys keeping this video short and sweet, hopefully it was a really good example as to how you can differentiate yourself against other candidates. You'll be surprised about how many candidates have no pet projects at all. Thanks for watching this video guys, cheers.

## Notes on extensions beyond the transcript

The SPEC.md goes beyond what the transcript describes. The video stops at database persistence; SPEC.md adds:

* The Greeks (delta, gamma, theta, vega, rho).
* Real market data via `yfinance`.
* Multiple pricing models (binomial, Monte Carlo) and convergence comparison.
* Backtesting on historical data.
* Production deployment.

These are project decisions made between Mustafa and Claude during the brainstorming phase, not from the source video.
