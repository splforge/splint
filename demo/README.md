# Recording the splint demo GIF

The GIF in the main README is produced from `demo/record.sh` via
[asciinema](https://asciinema.org/) + [agg](https://github.com/asciinema/agg).

## One-time setup

```bash
# macOS
brew install asciinema agg

# or pipx for asciinema, and grab the agg binary from its releases page
pipx install asciinema
```

Make sure splint is installed so it's on PATH:

```bash
pip install -e .
```

## Record

Run the script once on its own to check timing/colours:

```bash
./demo/record.sh
```

Tune the pace with env vars if needed: `TYPE_SPEED=0.03 PAUSE=1.2 ./demo/record.sh`.

Then record and render:

```bash
asciinema rec splint.cast -c "./demo/record.sh"
agg splint.cast docs/demo.gif --theme monokai --font-size 22
```

Reference it from the top of `README.md`:

```markdown
![splint in action](docs/demo.gif)
```

Tips for a crisp GIF:

- Use a wide-ish terminal (~100 cols) so lines don't wrap.
- A dark theme (`monokai`, `dracula`) makes the coloured severities pop.
- Keep it under ~25 s — trim dead air by lowering `PAUSE`.

## Bonus: the "real detections" money shot

Far more convincing than toy files — run splint over Splunk's own detection
library and show the count. Add this block to `record.sh` (or record a second
clip) once you've cloned the corpus:

```bash
git clone --depth 1 https://github.com/splunk/security_content.git
# extract each detection's `search:` field into *.spl, then:
splint security_content/**/*.spl --format json \
  | python -c "import sys,json,collections as c; d=json.load(sys.stdin)['diagnostics']; \
print(c.Counter(x['code'] for x in d))"
```

On 2114 real detections this surfaces a tight set of genuine performance
warnings (≈53 join, 9 transaction, 23 unbounded sort) — a great headline number
for the launch post.
