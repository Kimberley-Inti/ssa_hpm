# Candidate integration and release procedure

Integration is gated by the final stage11 validation summary. Until that gate
passes, main, existing tags and the nine earlier draft PRs stay unchanged.

The dependency order is PR#1 (stage2), #2 (stage3), #3 (stage4), #4 (stage5),
#5 (stage6), #6 (stage7), #7 (stage8), #8 (stage9), #9 (stage10), then stage11.
All are in Kimberley-Inti/ssa_hpm. External Chipyard/Rocket forks are not merged.
Stage11 initially targets stage10 so that review shows only the final review,
benchmark, evidence and documentation additions.

After acceptance, for each PR in order:

1. Re-read its head SHA, ownership, open state and diff. Its predecessor must
   already be merged; retarget this PR to main and check the remaining diff.
2. Remove draft status and use a merge commit, preserving original commits.
   Do not squash, rebase, force-push, delete stage branches or rewrite tags.
3. Re-read the merge result and main ancestry before proceeding.

Finally compare main's complete tree with the accepted stage11 tree and repeat
public patch/manifest/ROM verification. An identical tree does not require
another hardware simulation. A changed implementation requires affected tests.
Only then create an unused version tag and GitHub release in the private repo.
The release contains source patches, tests, small textual evidence and pinned
reproduction instructions, not full upstream trees, images or design PDFs.
Record the tag, main SHA/tree, release URL, visibility and remote read-back.

Source branches are references to tested source commits, not dependencies on
those commits being remotely fetchable. Reproduction fetches the pinned public
Chipyard/Rocket/Linux/OpenSBI baselines and applies the ordered project patches.
The development gitlink matches the recorded Rocket source commit. Distributed
Chipyard patches intentionally retain the fetchable public Rocket gitlink, while
the nested checkout receives the Rocket patches. Verify its expected tree/ROM
instead of expecting the reconstructed commit SHA to match a local development
SHA. No submodule operation may restore/overwrite that patched nested checkout.
