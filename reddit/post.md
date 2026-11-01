## Title

[OC] How every country is governed, on eight features instead of "democracy or not": 112 distinct systems, and 80 countries have one nobody else shares

## Body

I classified all 197 states (UN members plus the Holy See, Palestine, Taiwan and Kosovo) on eight features: kind of head of state, how that office is filled, executive type (including premier-presidential against president-parliamentary semi-presidentialism), whether head of state and head of government are one office, federal or unitary, one or two chambers, the lower-house electoral system, and power sharing by community. Every field comes from two sources, V-Dem v16 and the CIA World Factbook, compared cell by cell, plus 83 hand decisions with citations for the hard cases (UK devolution, Switzerland, Iran, Bosnia, Lebanon, the Vatican, Andorra, Malaysia, the UAE, juntas and transitional governments).

The map colours 12 families, shaded by electoral system, with stripes for federations. A few things I found: presidential and parliamentary republics each hold just over a quarter of humanity; 25 federations hold 41%; India shares its exact system with Pakistan and Ethiopia, the US with Nigeria; France has exactly the same constitutional form as the Republic of the Congo, which is why I keep form and freedom separate (V-Dem liberal democracy 0.80 against 0.12). Descriptively, 71% of PR countries are democracies against 43% of majoritarian ones. Interactive map with a card for every country, its sources and a "systems like this" button: https://maps.tristanhotham.com/government-types/

## Source comment

Sources: V-Dem Country-Year Dataset v16 (Coppedge et al. 2026, CC BY-SA 4.0), latest year 2025, for Regimes of the World, democracy indices and institutional indicators; CIA World Factbook 2026 and December 2024 editions (public domain, via factbook.json) for constitutional labels, legislatures and electoral systems; World Bank population 2025; Natural Earth boundaries. Typologies flatten degrees, the semi-presidential subtype rests partly on an expert-coded threshold, and links with democracy are descriptive, not causal.

Tools: Python (pandas, shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/government-types/
Paper: https://doi.org/{10.5281/zenodo.23863540}
Blog post: {https://blog.tristanhotham.com/2026/10/31/government-types/}
