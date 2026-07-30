# Mahesh Raju

**Decision-systems engineer.** I build the models that operations and demand
teams actually run on — simulation, optimization, and forecasting systems that
turn messy operational data into decisions with a dollar figure attached.

Day job: sole technical owner of 12+ production decision tools at a Caterpillar
manufacturing facility — capacity planning, machine and labor allocation, demand
fulfillment — in Python and SQL on Snowflake. M.S. Industrial & Systems
Engineering (simulation modeling, linear programming, decision analysis).

The repositories below are built on **synthetic data** so they can be public.
Each one is engineered the way the production version would be: tests that
assert the thing that matters, CI across three Python versions, and results
stated with the assumption that produced them.

---

### [remarketing-demand-lab](https://github.com/maheshrajuofficial-ops/remarketing-demand-lab)
**Demand science: elasticity, forecasting, segmentation, market sizing.**

A world generated from *planted* parameters, so every estimator can be graded on
whether it recovers them.

> Fitting `log(units)` on `log(price)` returns an elasticity **less than half**
> the truth — because price is chosen by people who can see demand. Adding fixed
> effects, trend and seasonality barely helps; the problem is simultaneity, not
> confounding. Two-stage least squares instrumented on auction acquisition cost
> recovers **every** model inside its 95% interval.

dbt Core · DuckDB · PySpark · statsmodels · rolling-origin backtesting (MASE
0.86 vs seasonal-naive) · segmentation scored by adjusted Rand (0.88) ·
TAM/SAM/SOM with the turnover assumption attached

### [manufacturing-automation-evaluator](https://github.com/maheshrajuofficial-ops/manufacturing-automation-evaluator)
**Seven-agent Claude Code decision system over a deterministic scoring engine.**

Evaluates automation investments against a fixed $30,000 capital gate and
produces dollar-denominated recommendations — payback, NPV, IRR.

> The cobot loses. Best demo, second-best payback, and it still ranks fourth:
> it eats 97% of the budget and needs a fixture and a taught program for every
> part number. A used bar feeder wins and leaves $13,600 unspent.

Hard gate applied *before* scoring · absolute anchors so padding a shortlist
can't inflate an incumbent · 125-case sensitivity sweep that reports how often
the recommendation survives its own assumptions

### [smart-factory-analytics](https://github.com/maheshrajuofficial-ops/smart-factory-analytics)
**Production-planning primitives: BOM explosion, demand, machine-hour allocation.**

Four allocation planners — equal-split, water-fill, greedy, sequenced — validated
by invariant-based property tests over randomized problem instances.

> Equal split "meets" 95% of demand by loading machines to **303%** of capacity.
> The capacity-respecting planners agree the shift is genuinely ~35% short, and
> name the operations to escalate.

Invariants asserted on every plan: no machine over capacity, and
`allocated + unmet == required` for every operation

### [snowflake-project-ticketing](https://github.com/maheshrajuofficial-ops/snowflake-project-ticketing)
**Streamlit-in-Snowflake app for projects, tasks and logged hours.**

Role-based access, PBKDF2 credential hashing, and a SQLite adapter that runs the
Snowpark application locally — so the app is testable and demonstrable without a
Snowflake account.

---

### Stack

`Python` `SQL` `Snowflake` `dbt` `DuckDB` `PySpark` `Streamlit` `Power BI`
`scikit-learn` `statsmodels` `pytest` `GitHub Actions` `Claude Code`

### Reach me

[LinkedIn](https://linkedin.com/in/maheshraju25) · mahesh.raju.official@gmail.com
