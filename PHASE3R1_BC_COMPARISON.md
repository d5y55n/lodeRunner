# B/C Full-Map Comparison

B widths 1/2 and C reversals 0.003/0.005 use exactly the A timestamps, price close,
850-day window and event-level future outcomes. B/C have no native A score.
Their raw counts, distances, density, clusters, overlap and age are compared
descriptively. C's window-local initialization is preserved by proven state
synchronization, not replaced with a global-history strategy.

Illustrative geometry contrasts (high-minus-low frozen bucket TP fraction):

| phase | config | feature | high_minus_low | nondecreasing | nonincreasing |
|---|---|---|---|---|---|
| development | ('A', {}) | clusters | -0.0475 | False | False |
| development | ('A', {}) | distance_difference | 0.0023127 | False | False |
| development | ('A', {}) | imbalance | 0.015979 | False | False |
| development | ('B', {'width': 1}) | clusters | -0.03896 | False | False |
| development | ('B', {'width': 1}) | distance_difference | 0.01047 | False | False |
| development | ('B', {'width': 1}) | imbalance | 0.006151 | False | False |
| development | ('B', {'width': 2}) | clusters | -0.048125 | False | False |
| development | ('B', {'width': 2}) | distance_difference | -0.015901 | False | False |
| development | ('B', {'width': 2}) | imbalance | 0.0059405 | False | False |
| development | ('C', {'reversal_fraction': 0.003}) | clusters | -0.039602 | False | False |
| development | ('C', {'reversal_fraction': 0.003}) | distance_difference | 0.012318 | False | False |
| development | ('C', {'reversal_fraction': 0.003}) | imbalance | 0.0086407 | False | False |
| development | ('C', {'reversal_fraction': 0.005}) | clusters | -0.03788 | False | False |
| development | ('C', {'reversal_fraction': 0.005}) | distance_difference | 0.0035273 | False | False |
| development | ('C', {'reversal_fraction': 0.005}) | imbalance | 0.021138 | False | False |
| replication | ('A', {}) | clusters | 0.010146 | True | False |
| replication | ('A', {}) | distance_difference | -0.023411 | False | False |
| replication | ('A', {}) | imbalance | 0.027296 | True | False |
| replication | ('B', {'width': 1}) | clusters | 0.0057234 | True | False |
| replication | ('B', {'width': 1}) | distance_difference | -0.006459 | False | False |
| replication | ('B', {'width': 1}) | imbalance | 0.01921 | False | False |
| replication | ('B', {'width': 2}) | clusters | 0.015425 | True | False |
| replication | ('B', {'width': 2}) | distance_difference | -0.013396 | False | False |
| replication | ('B', {'width': 2}) | imbalance | 0.015798 | False | False |
| replication | ('C', {'reversal_fraction': 0.003}) | clusters | -0.0079473 | False | True |
| replication | ('C', {'reversal_fraction': 0.003}) | distance_difference | 0.0075114 | False | False |
| replication | ('C', {'reversal_fraction': 0.003}) | imbalance | 0.022834 | False | False |
| replication | ('C', {'reversal_fraction': 0.005}) | clusters | -0.0059472 | False | True |
| replication | ('C', {'reversal_fraction': 0.005}) | distance_difference | 0.017992 | False | False |
| replication | ('C', {'reversal_fraction': 0.005}) | imbalance | 0.014679 | False | False |

All grid/configuration rows are in `reports/curve-shapes.csv`; quarter results
are separate. Baselines are identical unconditioned event periods, not isolated
zone interactions. Curves from the same underlying hours are dependent. Block
intervals are not independent detector-vs-detector tests, and no detector is ranked
as superior from a larger conditional fraction. Results remain exploratory.
