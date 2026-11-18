# Paper

LaTeX source for the technical report *EUROPA Alignment: A Transparent, Parallel Safety Benchmark for 36 European Languages*.

```bash
python3 paper/analysis.py          # regenerates paper/generated/* and paper/figures/* from results/runs/
cd paper && tectonic europa-alignment.tex
cp europa-alignment.pdf ../docs/paper/europa-alignment.pdf
```

`analysis.py` needs numpy and matplotlib. Every number in the paper comes from `generated/macros.tex`.
