# Maintaining the AIRBDS assessment skills

This document is for **maintainers** of the assessment skills. People who only
want to *use* a skill need none of this — see [`../README.md`](../README.md).

## Release channels

The assessment skill is developed in channels:

- `development/` — the working copy under active development.
- `testing/` — the copy promoted to a testing release.
- `production` — **not a directory here.** The production bundle is the `testing`
  build with its release channel rewritten, published to
  [AIBIO-UK/airbds-core](https://github.com/AIBIO-UK/airbds-core) as
  `skills/airbds-assessment-skill.zip`. See
  [Promoting to production](#promoting-to-production).

Each channel evolves independently: `testing` may sit on an older AIRBDS metric
version while `development` has moved ahead.

> **Why production has no source directory.** A third copy of `SKILL.md`
> differing from `testing` by one word is exactly the kind of duplication that
> drifts, and it would need a third build workflow publishing a
> "production" release from a repo that is not where production lives. Deriving
> it at release time instead means the production bundle exists in one place
> only — `airbds-core` — so there is no second copy to get out of step.

## The version manifest (`versions.json`)

`skills/versions.json` is the source of truth for the **current** assessment
skill on each channel. It is served over GitHub raw at
<https://raw.githubusercontent.com/AIBIO-UK/airbds-dev/main/skills/versions.json>.

> **Why `airbds-dev` and not the publication repo?** The `testing` and
> `development` channels are development artifacts: the build workflows in this
> repo publish their zips as releases *here*, so the manifest and the
> `skill_update_url`s must point here too.
>
> These URLs once pointed at `airbds-metric`, which worked only while that was
> this repo's name. This repo was renamed to `airbds-dev`, a new placeholder repo
> was created at the vacated `airbds-metric` name, and that severed GitHub's
> rename redirect and left the update check returning 404.
>
> That placeholder has since been renamed again, to `AIBIO-UK/airbds-core`, which
> is now the publication repo. Two consequences are worth knowing before you
> touch any URL here:
>
> - `AIBIO-UK/airbds-metric` now **301s to `airbds-core`** — so a surviving old
>   link lands on the publication repo, not on this one.
> - Freeing the `airbds-metric` name did **not** restore this repo's original
>   rename redirect. It was verified still broken immediately after the rename:
>   `raw.githubusercontent.com/AIBIO-UK/airbds-metric/main/skills/versions.json`
>   returns 404. Severed redirects do not come back; do not plan around one.
>
> A future *released* channel is expected to be served from `airbds-core`.
> **Do not repoint these URLs until that repo actually hosts a `versions.json`
> and the corresponding releases** — a redirect resolving is not the same as the
> file being there, and the update check breaks again if it isn't. Note that the
> URL is baked into each published skill zip, so a stranded skill cannot be
> repaired retroactively — only reinstallation picks up a new URL.

Each entry under `channels` records, for that channel's current skill:

- `metric_version` — the AIRBDS metric version it assesses against;
- `skill_version` — its skill version;
- `skill_update_url` — where a user gets the latest build.

## How the runtime update check works

At start-up an assessment skill makes a **best-effort** fetch of this manifest
and compares the manifest's `metric_version` for **its own channel only**
against its own metric version — the `schema_version` field of its bundled
metric file (`assets/airbds_metric.json`):

- If the manifest is **strictly newer**, the skill pauses and **asks the user**
  whether to proceed with the older bundled metric or stop and update to the
  newer skill first — it does not start the assessment until they choose.
- If the fetch **fails** (no network, unsupported, error, timeout) it is
  silently skipped — a failed fetch never blocks an assessment.
- A skill never looks at other channels, so a `testing` skill is **not** nudged
  when `development` moves ahead.

For this to work, each skill declares its channel in its `SKILL.md` frontmatter
and bundles the metric file whose `schema_version` is the version it assesses
against. Keep the manifest's `metric_version` for a channel in step with that
bundled `schema_version`. Neither channel's skill carries a `metric_version`
frontmatter field any more — both derive their metric version from the bundled
`schema_version`.

The channel and skill version live **under `metadata`** —
`metadata.channel`, `metadata.version`. The Agent Skills specification defines a
closed set of top-level frontmatter fields (`name`, `description`, `license`,
`compatibility`, `metadata`, `allowed-tools`) and `metadata` is the mapping
provided for everything else, so a conformant client is entitled to reject a
skill that puts its own keys at the top level. `channel` is read by the skill
itself for the update check, so a client that dropped it would break that check
silently. Validate with the reference library before publishing:

```bash
pip install skills-ref   # provides the `agentskills` command
agentskills validate skills/development/airbds-assessment-skill
```

Note it parses frontmatter with StrictYAML, which is stricter than YAML proper:
inline flow style (`tags: [science]`) is rejected, so use block sequences.

**`metadata.hermes` is deliberately non-conformant — leave it nested.** The spec
describes `metadata` as a map of string keys to *string* values, so a strict
reader flattens the nested block to a string (`agentskills read-properties`
returns `"{'tags': ['science'], 'category': 'science'}"` — a Python repr, not
even valid JSON). It is kept nested because that is the shape Hermes' own skill
files use, and Hermes reads it with an ordinary YAML parser, which yields the
structure intended. Flattening to `hermes-tags` / `hermes-category` would be
spec-clean but would stop matching what Hermes expects. Revisit only if Hermes
documents a different layout.

Both channels follow this layout.

## Keeping the manifest in step

Bump a channel's `metric_version` in `versions.json` **only when that channel's
skill is actually repointed to a new metric** — i.e. when you repoint the skill's
bundled `assets/airbds_metric.json` symlink at a new `metric/airbds_metric_v*.json`
(so its `schema_version` changes). Leave a channel untouched if it intentionally
stays on the older metric. A stale entry will either suppress a needed update
prompt or nag users who are already current.

**A new metric is at least a MINOR skill bump — never a patch.** When a channel
moves to a new metric, raise its `skill_version` by at least a minor: `0.8.1`
becomes `0.9.0`, not `0.8.2`. The bundle's contents have changed and it now
scores against a different metric, so two builds separated only by a patch number
would look interchangeable when they are not. Raise it in **both** places that
carry it — `versions.json` and that channel's `SKILL.md` `metadata.version` — and
note that the runtime update prompt keys off `metric_version`, not
`skill_version`, so the bump is about honest identity rather than triggering the
prompt.

When a metric version bump is the trigger, follow
[`RELEASING.md`](../../RELEASING.md), which puts this step in order against the
rest of the release — the metric is published first, and the skill channels are
repointed at it afterwards.

`channels.production` is the exception to "bump when the skill changes": nothing
in this repo changes what production serves, so its entry moves only when a
promotion is actually made — and it is bumped *before* running the release
script, which refuses to publish a zip that entry does not advertise.

Record every skill version bump — and every channel promotion — under the
**Assessment skill** section of [`CHANGELOG.md`](../../CHANGELOG.md), with a
heading naming the version and the channel(s) it applies to. Skill versions are
tracked separately from metric versions there, because the two move
independently.

## Release builds (GitHub Actions)

Each channel's downloadable skill zip is built and published by a GitHub Actions
workflow:

- `testing` → [`.github/workflows/build-assessment-skill-for-test.yml`](../../.github/workflows/build-assessment-skill-for-test.yml)
  (release tag `assessment-skill-testing`, asset `airbds-assessment-skill-testing.zip`).
- `development` → [`.github/workflows/build-assessment-skill-for-development.yml`](../../.github/workflows/build-assessment-skill-for-development.yml)
  (release tag `assessment-skill-development`, asset `airbds-assessment-skill-development.zip`).

Each pushes on `main`, zips its channel's skill directory (dereferencing the
symlinked metric/template into real files), and recreates its release so the
`skill_update_url` in `versions.json` always serves the latest build.

**These workflows are coupled to the skill directory structure — keep them in
step when it changes.** In particular, if you rename or restructure a skill's
bundle directory (e.g. the `templates/` → `assets/` move), update, for the
affected channel's workflow:

- the `on.push.paths` filter (so the right files actually trigger a rebuild — a
  stale path silently stops builds firing), and
- the `zip` step and its comment (so the new structure is what gets packaged).

A workflow file only takes effect once it's merged to the default branch, since
Actions runs the version of the workflow on `main`. Both build workflows also
support `workflow_dispatch`, so you can trigger a rebuild manually from the
Actions tab without a code change.

## Validation

`versions.json` is checked in CI by the `validate-skills-versions` workflow,
which runs [`skills/src/scripts/validate_skills_versions.py`](../src/scripts/validate_skills_versions.py).
It confirms the manifest is valid JSON, every channel has the required fields,
and every advertised `metric_version` has a matching
`metric/airbds_metric_v<version>.yaml`.

It then **cross-checks each channel against the bundle it describes**, which is
the part that catches the mistakes this page warns about: `skill_version` against
that channel's `SKILL.md` `metadata.version`, `metadata.channel` against the
directory the skill sits in, and `metric_version` against the `schema_version` of
the metric its `assets/airbds_metric.json` symlink actually resolves to. A
repointed symlink with an unbumped manifest — or a bumped manifest with an
unmoved symlink — fails here rather than shipping a skill that misreports what it
scored against. `production` is skipped, having no source directory.

Given `--since <git-ref>` it also enforces the minor-bump rule above, comparing
the manifest to its state at that ref. Run it locally before committing a
manifest change:

```
python3 skills/src/scripts/validate_skills_versions.py --since HEAD
```

CI resolves the ref itself — the branch point for a pull request, the preceding
commit for a push — and falls back to the stateless checks when there is no
usable baseline.

## Promoting development to testing

`development` is the working copy; `testing` is a snapshot of it taken when a
build is judged ready to test. A channel bundle carries its channel *inside* it —
`metadata.channel` in `SKILL.md`, plus the update-check prose naming which
`channels.<name>` entry to read — so promoting is not a plain copy: the channel
token has to be substituted, the symlinked metric and template must stay symlinks
(so `testing` keeps tracking the current files rather than freezing a copy), and
`skills/versions.json`'s `testing` entry has to be moved to describe what was just
promoted. This was done by hand, and every part of it was easy to get subtly
wrong.

One script does the whole thing and prints exactly what it changed:

```bash
./skills/src/scripts/promote_skill_channel.py --dry-run   # rehearse
./skills/src/scripts/promote_skill_channel.py             # do it
./skills/src/scripts/promote_skill_channel.py --check     # is testing already this promotion?
```

It reuses `rechannel_skill_zip.rewrite_text`, so the channel substitution carries
the same reversibility proof used when the production zip is derived at release
time — only the channel changed. `--from`/`--to` default to
`development`/`testing` but take any pair of existing channels.

Then review the diff, run `validate_skills_versions.py`, and commit. Pushing to
`main` triggers the `testing` build workflow, which republishes the release the
`skill_update_url` points at. The script does **not** commit, build, or push —
those stay deliberate, as everywhere else in the release path.

`--check` exits 0 whether or not a promotion is pending: `testing` is *meant* to
lag `development` between promotions, so a difference is information, not a fault.

## Promoting to production

The `testing` and `development` channels are staging: their zips are published as
releases *in this repo*. Production is the publication repository,
[AIBIO-UK/airbds-core](https://github.com/AIBIO-UK/airbds-core), where the skill
lives at `skills/airbds-assessment-skill.zip` — no channel and no version in the
filename.

Promotion is one step, which both produces the production bundle and opens the
pull request that publishes it. There is no production zip in this repo to fall
out of step with the one in `airbds-core`:

```bash
./skills/src/scripts/release_skill_to_core.sh --dry-run   # rehearse
./skills/src/scripts/release_skill_to_core.sh             # branch, push, PR
```

Order of operations, because the script enforces it:

1. Promote `development` → `testing` (see
   [Promoting development to testing](#promoting-development-to-testing)) and let
   the `testing` build workflow republish the release.
2. Set `channels.production` in `versions.json` to the version being promoted,
   and commit it. The script gates on **that** entry, not on `testing`, because
   `channels.production` is what an installed production skill polls; publishing
   a zip it does not advertise ships a version nothing announces.
3. Run the script.

### The channel rewrite

The script starts from the `testing` release asset — the artifact people have
actually been testing — and changes exactly one thing in it: the release channel.
That step cannot be skipped. A bundle carries its channel *inside* it
(`metadata.channel`, plus the prose naming which `channels.<name>` entry to read),
so publishing the tested bytes untouched tells every production user, and the
runtime update check, that they are on `testing` — which is how the zip currently
in `airbds-core` came to claim the wrong channel.

So the old byte-for-byte guarantee is not available, and is replaced by a
verified one:
[`skills/src/scripts/rechannel_skill_zip.py`](../src/scripts/rechannel_skill_zip.py)
substitutes the channel token in `SKILL.md`, copies every other member verbatim
(same bytes, times, and permissions), and then proves the result is only that:
undoing the substitution must reproduce the tested `SKILL.md` byte for byte. It
refuses if the source bundle already mentions `production` anywhere, because that
is the one case where the substitution could not be undone — and so the one case
where "only the channel changed" could not be checked. Reword the mention and
rebuild the `testing` release.

A reviewer can audit the published zip without trusting any of this:

```bash
skills/src/scripts/rechannel_skill_zip.py \
  --in airbds-assessment-skill-testing.zip --check airbds-assessment-skill.zip
```

See [`skills/src/README.md`](../src/README.md) for the full behaviour.

### The README stamp

`airbds-core`'s `skills/README.md` tells a reader which skill version they are
about to download and which metric it scores against. Those numbers are part of
the release, not commentary on it, so the release commit carries them: the same
PR that lands the zip restamps that sentence via
[`scripts/stamp_core_versions.py`](../../scripts/stamp_core_versions.py), run
through `publish-to-core.sh`'s `--post-copy` hook.

The numbers sit inside HTML comment markers in the README source:

```markdown
currently at version <!--skill-version-->0.8.0<!--/skill-version--> and assessing
against [AIRBDS metric](...) v<!--metric-version-->1.0.0<!--/metric-version-->
```

Comments render as nothing, so the published page reads exactly as it always
did — the markers exist only to give the stamper an unambiguous target, instead
of a regex hunting version-shaped strings through prose that will be reworded
eventually.

Two consequences worth knowing:

- **A missing marker fails the release.** If the README has been rewritten
  without its markers, the hook exits non-zero and nothing is pushed. That is
  deliberate: silently skipping the stamp would publish the stale sentence this
  machinery exists to prevent. Restore the markers and re-run.
- **A stale README is on its own reason to release.** The stamp runs before the
  "already identical" check, so re-running a promotion whose zip has not changed
  still opens a PR if the prose has drifted.

The metric release ([`metric/src/scripts/release_metric_to_core.sh`](../../metric/src/scripts/release_metric_to_core.sh))
does **not** touch this file. It stamps the metric version into `airbds-core`'s
**top-level `README.md`** instead (its "current version" line), with
`--file README.md` — so the metric and skill PRs edit different files and never
collide. That collision is what once let a skill PR slip through unmerged behind
a hand-resolved README conflict. Each release owns one README: the skill release
this `skills/README.md`, the metric release the top-level one.

> `versions.json` itself still lives in **this** repo and is still served from
> the `raw_url` baked into every published skill, including the production one —
> publishing to `airbds-core` does not move it, and the file's own
> `_comment_urls` explains why it must not move until `airbds-core` actually
> hosts it. What *does* point at `airbds-core` is
> `channels.production.skill_update_url`, because that is where the production
> zip genuinely is. The `testing` and `development` URLs still point at this
> repo's releases.
