import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import type { ReactNode } from 'react';

import styles from './index.module.css';

function Hero(): ReactNode {
  return (
    <section className={styles.hero}>
      <div className={styles.heroGrid}>
        <div>
          <h1 className={styles.heroTitle}>
            Code<em className={styles.heroTitleAccent}>Leash</em>
          </h1>
        </div>
        <div className={styles.heroRight}>
          <p className={styles.tagline}>Your coding agent, on a leash</p>
          <p className={styles.heroDesc}>
            An opinionated, full stack framework & toolkit for high quality
            software development using Claude Code. Architectural constraints,
            automated code quality checking & guidance for fixing issues. Helps
            Claude Code generate high quality code. NOT an AI agent
            orchestrator!
          </p>
          <div className={styles.heroCta}>
            <Link to="/docs/" className={styles.btnPrimary}>
              Get Started
            </Link>
            <Link
              href="https://github.com/cadamsdotcom/CodeLeash"
              className={styles.btnGhost}
            >
              See the Code
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

function StateStrip(): ReactNode {
  return (
    <div className={styles.stateStrip}>
      <div className={styles.stateStripInner}>
        <span className={`${styles.stateNode} ${styles.stateNode}`}>BEGIN</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateLabel}>write tests</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateNode}>watch tests fail</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={`${styles.stateNode} ${styles.stateNodeRed}`}>
          red
        </span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateLabel}>write code so tests pass</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateNode}>watch tests pass</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={`${styles.stateNode} ${styles.stateNodeGreen}`}>
          green
        </span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={`${styles.stateNode} ${styles.stateNode}`}>
          REPEAT
        </span>
      </div>
    </div>
  );
}

function LeashComparison(): ReactNode {
  return (
    <section className={styles.leashComparison}>
      <div className={styles.container}>
        <div className={styles.leashGrid}>
          <div className={styles.leashCard}>
            <h3 className={styles.leashHeadingBad}>Coding agent off leash:</h3>
            <div className={styles.leashImageWrap}>
              <img
                src="/img/leash-dont-walk.jpg"
                alt="Frustrated person telling their dog not to walk on the road - the dog ignores them"
                className={styles.leashImage}
              />
            </div>
          </div>
          <div className={styles.leashCard}>
            <h3 className={styles.leashHeadingGood}>With a leash:</h3>
            <div className={styles.leashImageWrap}>
              <img
                src="/img/leash-cant-walk.jpg"
                alt="Happy person walking their dog on a leash - the dog can't walk on the road"
                className={styles.leashImage}
              />
            </div>
          </div>
        </div>
        <p className={styles.leashDesc}>
          I'm{' '}
          <a
            href="https://linkedin.com/in/cadamsdotcom"
            target="_blank"
            rel="noreferrer"
          >
            Chris
          </a>
          . I've been a software engineer for over 20 years.
        </p>
        <p className={styles.leashDesc}>
          Claude Code writes all code for my product,{' '}
          <a href="https://approviq.com" target="_blank" rel="noreferrer">
            ApprovIQ
          </a>{' '}
          - with{' '}
          <a
            href="https://github.com/cadamsdotcom/CodeLeash/commit/859910f86cd01d4fb8512a305d0c5cc6d231684c"
            target="_blank"
            rel="noreferrer"
          >
            no em-dashes
          </a>
          !
        </p>
        <p className={styles.leashDesc}>
          Agents go off the rails. They get distracted. Asking nicely with
          AGENTS.md and system prompts and interrupting their work to remind
          them of stuff... yeah, it works... sort of... most of the time. That's
          a problem, because, "most of the time" doesn't cut it for building
          serious software.
        </p>
        <p className={styles.leashDesc}>
          CodeLeash puts guardrails <em>outside</em> the agent, so it{' '}
          <em>can&apos;t</em> go off the rails, forget them or ignore them.
          While everyone and their dog is building the tallest tower of agent
          orchestration they can, I've been tightly controlling outcomes in
          ApprovIQ&apos;s codebase, by sharply defining what quality code looks
          like, rubbing Claude Code's nose in it with automation, and forcing it
          to fix its mistakes - all while I am off doing something else.
          CodeLeash enforces quality with code based hooks, scripts, tools, and
          loops, in a way the agent can&apos;t ignore or bypass.
        </p>
        <p className={styles.leashDesc}>
          Look at the images. Notice: "Can&apos;t walk on the road" is NOT in a
          speech bubble! A leash means never barking orders.
        </p>
        <p className={styles.leashDesc}>
          Agents today cannot do everything you ask while also doing their task.
          Create guardrails that automatically show how they failed to live up
          to your standards while guiding them to correct their mistakes. Hence
          the analogy of a leash.
        </p>
      </div>
    </section>
  );
}

function Features(): ReactNode {
  return (
    <section className={styles.features} id="features">
      <div className={styles.container}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionNumber}>01</span>
          <span className={styles.sectionTitle}>What's Inside</span>
        </div>
        {/* Cards cycle: Red, Earth(reversed), Green, Earth(reversed), Red...
            When adding/removing cards, shift colors to maintain the pattern. */}
        <div className={styles.featuresGrid}>
          <Link to="/docs/tdd-guard" className={styles.featureCardLink}>
            <div className={`${styles.featureCard} ${styles.featureCardRed}`}>
              <div className={styles.featureLeft}>
                <span
                  className={`${styles.featureNumber} ${styles.featureNumberRed}`}
                >
                  01
                </span>
                <div className={styles.featureIcon}>
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 36 36"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <rect
                      x="2"
                      y="2"
                      width="32"
                      height="32"
                      rx="2"
                      stroke="rgb(239 68 68)"
                      strokeWidth="2"
                      fill="none"
                    />
                    <path
                      d="M10 18L15 23L26 12"
                      stroke="rgb(34 197 94)"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <h3 className={styles.featureCardTitle}>
                  Enforcement of Test-Driven Development
                </h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  <a
                    href="https://medium.com/@bethqiang/the-absolute-beginners-guide-to-test-driven-development-with-a-practical-example-c39e73a11631"
                    target="_blank"
                    rel="noreferrer"
                  >
                    Test Driven Development
                  </a>{' '}
                  is almost a universal way to build software. Write failing
                  tests, watch them fail, write code to make them pass, watch
                  them pass. You're gradually building a repository of every
                  decision you ever made. Even better, if a decision is{' '}
                  <i>un-made</i>, tests fail. Alarms go off.
                </p>
                <p className={styles.featureCardDesc}>
                  Forcing the agent through TDD created a repository of all my
                  micro decisions - I stopped needing to repeat past decisions
                  to the agent. In time I began to be{' '}
                  <i>supervising the TDD process itself</i>, while the agent
                  built software according to its plan. I had gotten myself out
                  of the loop, removing a layer of tedium.
                </p>
                <p className={styles.featureCardDesc}>
                  But babysitting a TDD process is almost as tedious as doing
                  TDD! I was constantly stopping the agent - don't do that, you
                  didn't see the tests pass, roll that back, it's not time to
                  write code yet. The agent was frequently befuddled by this. So
                  I asked: can I get myself out of <i>that</i> loop too?
                </p>
                <p className={styles.featureCardDesc}>
                  The solution Claude and I hit on is a state machine tracked in
                  a local log file. You can see the state machine at the top of
                  the page!
                </p>
                <p className={styles.featureCardDesc}>
                  With CodeLeash, the agent MUST use TDD. A state machine
                  enforces the Red-Green-Refactor cycle and blocks file edits
                  until tests fail first. No shortcuts, no skipping ahead.
                </p>
                <p className={styles.featureCardDesc}>
                  A test suite in which the agent has seen every test fail -
                  then made each test pass by writing code - helps prevent
                  regressions and keeps development velocity high as your
                  product grows. Per-agent isolation lets agents run in
                  parallel.
                </p>
                <span
                  className={`${styles.featureLearnMore} ${styles.featureLearnMoreRed}`}
                >
                  Learn more{' '}
                  <span className={styles.featureLearnMoreArrow}>&rarr;</span>
                </span>
              </div>
            </div>
          </Link>

          <Link
            to="/docs/code-quality-checks"
            className={styles.featureCardLink}
          >
            <div
              className={`${styles.featureCard} ${styles.featureCardReversed} ${styles.featureCardEarth}`}
            >
              <div className={styles.featureLeft}>
                <span
                  className={`${styles.featureNumber} ${styles.featureNumberEarth}`}
                >
                  02
                </span>
                <div className={styles.featureIcon}>
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 36 36"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M6 8H30M6 14H24M6 20H28M6 26H20"
                      stroke="rgb(34 197 94)"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <h3 className={styles.featureCardTitle}>Code Quality Checks</h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  CodeLeash checks code quality using many small scripts,{' '}
                  <i>not</i> AI. No AI means zero tokens burned. No false
                  positives and no inconsistency. They&apos;re deterministic so
                  they're impossible to fool. And fast so you can run them every
                  time you change code.
                </p>
                <p className={styles.featureCardDesc}>
                  Check scripts exit 0 on success or non-zero on failure.
                  Failures print instructions for the agent to tell it how and
                  where to fix. Failure blocks the agent, and that forces it to
                  fix breakage right away.
                </p>
                <p className={styles.featureCardDesc}>
                  Checks run before every commit, blocking problems from ever
                  reaching your repository.
                </p>
                <p className={styles.featureCardDesc}>
                  CodeLeash is full of examples for your coding agent to crib
                  from. Some traverse the codebase with ASTs; others with
                  regexes. A surprising amount of the code review feedback
                  you've ever given in your software engineering career can be
                  automated - ask your agent for ideas! With a big enough
                  library of checks - built by you - once your agent stops
                  working, all the basic issues were removed in response to the
                  checks failing, without you watching. You no longer need to
                  see agent code with obvious flaws.
                </p>
                <p className={styles.featureCardDesc}>
                  Never repeat obvious fixes to your agent again.
                </p>
                <span
                  className={`${styles.featureLearnMore} ${styles.featureLearnMoreEarth}`}
                >
                  Learn more{' '}
                  <span className={styles.featureLearnMoreArrow}>&rarr;</span>
                </span>
              </div>
            </div>
          </Link>

          <Link to="/docs/self-reflection" className={styles.featureCardLink}>
            <div className={`${styles.featureCard} ${styles.featureCardGreen}`}>
              <div className={styles.featureLeft}>
                <span
                  className={`${styles.featureNumber} ${styles.featureNumberGreen}`}
                >
                  03
                </span>
                <div className={styles.featureIcon}>
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 36 36"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M18 4C12 4 7 9 7 15C7 21 12 24 12 28H24C24 24 29 21 29 15C29 9 24 4 18 4Z"
                      stroke="rgb(34 197 94)"
                      strokeWidth="2"
                      fill="none"
                    />
                    <path
                      d="M14 32H22"
                      stroke="rgb(34 197 94)"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                    <path
                      d="M18 12V20M14 16H22"
                      stroke="rgb(160 100 50)"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
                <h3 className={styles.featureCardTitle}>
                  Self-Reflection System
                </h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  Agents forget everything between sessions. Compaction destroys
                  knowledge and sessions end. Hard-won insights vanish. The same
                  mistakes are made again and again.
                </p>
                <p className={styles.featureCardDesc}>
                  CodeLeash hooks force your agent to capture learnings in files
                  before context is lost. When a session ends or context
                  compacts, the agent writes structured notes about surprises,
                  workflow friction, TDD discipline issues...
                </p>
                <p className={styles.featureCardDesc}>
                  Learnings can be used to make permanent improvements to your
                  codebase. A <code>/learnings</code> command completes the loop
                  -- integrating the best insights back into the codebase as
                  permanent improvements, and deleting the learnings files.
                </p>
                <span
                  className={`${styles.featureLearnMore} ${styles.featureLearnMoreGreen}`}
                >
                  Learn more{' '}
                  <span className={styles.featureLearnMoreArrow}>&rarr;</span>
                </span>
              </div>
            </div>
          </Link>

          <Link to="/docs/how-tests-work" className={styles.featureCardLink}>
            <div
              className={`${styles.featureCard} ${styles.featureCardReversed} ${styles.featureCardEarth}`}
            >
              <div className={styles.featureLeft}>
                <span
                  className={`${styles.featureNumber} ${styles.featureNumberEarth}`}
                >
                  04
                </span>
                <div className={styles.featureIcon}>
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 36 36"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <circle
                      cx="18"
                      cy="18"
                      r="15"
                      stroke="rgb(160 100 50)"
                      strokeWidth="2"
                      fill="none"
                    />
                    <path
                      d="M18 10V18L23 23"
                      stroke="rgb(160 100 50)"
                      strokeWidth="2.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
                <h3 className={styles.featureCardTitle}>
                  Strict Test Timeouts
                </h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  Each unit test must complete within 10ms. Forces tests to be
                  pure business logic - no I/O, no testing third-party code.
                </p>
                <p className={styles.featureCardDesc}>
                  This makes it hard for tests to interfere which allows
                  parallel test runs. If a test touches the network or spins up
                  a server, it fails.
                </p>
                <p className={styles.featureCardDesc}>
                  Auto-retry handles transient performance hiccups like JIT
                  warmup or heavy import chains. When a test times out on retry,
                  a flamegraph SVG is generated automatically so you can debug.
                  And I was surprised to learn: agents can fix code based on a
                  flamegraph!
                </p>
                <p className={styles.featureCardDesc}>
                  Your agent can test your entire product in under a minute. Let
                  it move fast and break things - then fix them.
                </p>
                <span
                  className={`${styles.featureLearnMore} ${styles.featureLearnMoreEarth}`}
                >
                  Learn more{' '}
                  <span className={styles.featureLearnMoreArrow}>&rarr;</span>
                </span>
              </div>
            </div>
          </Link>

          <Link
            to="/docs/worktree-parallel-work"
            className={styles.featureCardLink}
          >
            <div className={`${styles.featureCard} ${styles.featureCardRed}`}>
              <div className={styles.featureLeft}>
                <span
                  className={`${styles.featureNumber} ${styles.featureNumberRed}`}
                >
                  05
                </span>
                <div className={styles.featureIcon}>
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 36 36"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M8 8V28H28"
                      stroke="rgb(160 160 160)"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                    <path
                      d="M14 8V28"
                      stroke="rgb(224 224 224)"
                      strokeWidth="1"
                    />
                    <path
                      d="M20 8V28"
                      stroke="rgb(224 224 224)"
                      strokeWidth="1"
                    />
                    <path
                      d="M26 8V28"
                      stroke="rgb(224 224 224)"
                      strokeWidth="1"
                    />
                    <path
                      d="M8 14H28"
                      stroke="rgb(224 224 224)"
                      strokeWidth="1"
                    />
                    <path
                      d="M8 20H28"
                      stroke="rgb(224 224 224)"
                      strokeWidth="1"
                    />
                    <circle cx="14" cy="14" r="3" fill="rgb(160 100 50)" />
                    <circle cx="20" cy="20" r="3" fill="rgb(34 197 94)" />
                    <circle cx="26" cy="14" r="3" fill="rgb(239 68 68)" />
                  </svg>
                </div>
                <h3 className={styles.featureCardTitle}>
                  Worktree Isolation: Work On Many Features At Once
                </h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  Parallel development in git worktrees with full isolation
                  between them. Each worktree gets its own ports for everything.
                </p>
                <p className={styles.featureCardDesc}>
                  Work on many features at once without conflicts. Spin up a new
                  worktree, run ./init.sh && npm run dev, and enjoy a completely
                  independent development environment with no port collisions.
                </p>
                <span
                  className={`${styles.featureLearnMore} ${styles.featureLearnMoreRed}`}
                >
                  Learn more{' '}
                  <span className={styles.featureLearnMoreArrow}>&rarr;</span>
                </span>
              </div>
            </div>
          </Link>

          <Link
            to="/docs/full-stack-monorepo"
            className={styles.featureCardLink}
          >
            <div
              className={`${styles.featureCard} ${styles.featureCardReversed} ${styles.featureCardEarth}`}
            >
              <div className={styles.featureLeft}>
                <span
                  className={`${styles.featureNumber} ${styles.featureNumberEarth}`}
                >
                  06
                </span>
                <div className={styles.featureIcon}>
                  <svg
                    width="36"
                    height="36"
                    viewBox="0 0 36 36"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <rect
                      x="4"
                      y="4"
                      width="12"
                      height="12"
                      rx="2"
                      stroke="rgb(160 100 50)"
                      strokeWidth="2"
                      fill="none"
                    />
                    <rect
                      x="20"
                      y="4"
                      width="12"
                      height="12"
                      rx="2"
                      stroke="rgb(34 197 94)"
                      strokeWidth="2"
                      fill="none"
                    />
                    <rect
                      x="12"
                      y="20"
                      width="12"
                      height="12"
                      rx="2"
                      stroke="rgb(239 68 68)"
                      strokeWidth="2"
                      fill="none"
                    />
                    <path
                      d="M16 10H20M10 16V20M26 16V20"
                      stroke="rgb(160 160 160)"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeDasharray="2 2"
                    />
                  </svg>
                </div>
                <h3 className={styles.featureCardTitle}>
                  Full-stack & Built To All Work Together
                </h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  One repo has all your backend and frontend code. Simple data
                  type sharing between pydantic and TypeScript.
                </p>
                <p className={styles.featureCardDesc}>
                  One server (uvicorn) serves your app in production. React
                  assets are built with Vite, minified, and served statically.
                </p>
                <p className={styles.featureCardDesc}>
                  Your agent can atomically commit backend and frontend changes
                  in one commit. No more coordination across repos, no deploy
                  ordering issues, and no IDLs. Just JSON based REST APIs with
                  shared data types between backend and frontend. Bliss!
                </p>
                <span
                  className={`${styles.featureLearnMore} ${styles.featureLearnMoreEarth}`}
                >
                  Learn more{' '}
                  <span className={styles.featureLearnMoreArrow}>&rarr;</span>
                </span>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </section>
  );
}

function Quickstart(): ReactNode {
  return (
    <section className={styles.quickstart} id="quickstart">
      <div className={styles.container}>
        <div className={styles.quickstartGrid}>
          <div>
            <h2 className={styles.quickstartHeading}>
              Two commands to see the
              <br />
              <em className={styles.quickstartAccent}>hello world demo.</em>
            </h2>
            <p className={styles.quickstartDesc}>
              init.sh installs dependencies, starts Supabase, configures your
              environment, and installs the pre-commit hook. Then dev starts
              Vite and FastAPI with hot reload.
            </p>
          </div>
          <div>
            <div className={styles.codeBlock}>
              <span className={styles.codePrompt}>$ </span>
              ./init.sh && npm run dev
              <span className={styles.codeComment}>
                # &rarr; http://localhost:8000
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TechStack(): ReactNode {
  type Category = 'language' | 'framework' | 'platform';

  const categoryClass: Record<Category, string> = {
    language: styles.stackTagLanguage,
    framework: styles.stackTagFramework,
    platform: styles.stackTagPlatform,
  };

  const rows: {
    label: string;
    tags: { name: string; category: Category }[];
  }[] = [
    {
      label: 'Database',
      tags: [
        { name: 'Supabase', category: 'platform' },
        { name: 'PostgreSQL', category: 'platform' },
      ],
    },
    {
      label: 'Auth',
      tags: [{ name: 'Supabase Auth', category: 'platform' }],
    },
    {
      label: 'Backend',
      tags: [
        { name: 'Python', category: 'language' },
        { name: 'FastAPI', category: 'framework' },
      ],
    },
    {
      label: 'Frontend',
      tags: [
        { name: 'React', category: 'framework' },
        { name: 'TypeScript', category: 'language' },
        { name: 'Vite', category: 'framework' },
        { name: 'Tailwind CSS', category: 'framework' },
      ],
    },
    {
      label: 'Testing',
      tags: [
        { name: 'pytest', category: 'framework' },
        { name: 'Vitest', category: 'framework' },
        { name: 'Playwright', category: 'framework' },
      ],
    },
    {
      label: 'Observability',
      tags: [
        { name: 'Prometheus', category: 'platform' },
        { name: 'OpenTelemetry', category: 'framework' },
        { name: 'Sentry', category: 'platform' },
      ],
    },
  ];

  return (
    <section className={styles.stack}>
      <div className={styles.container}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionNumber}>02</span>
          <span className={styles.sectionTitle}>Stack</span>
        </div>
        <div className={styles.stackRows}>
          {rows.map(row => (
            <div key={row.label} className={styles.stackRow}>
              <span className={styles.stackRowLabel}>{row.label}</span>
              <div className={styles.stackRowTags}>
                {row.tags.map(tag => (
                  <span
                    key={tag.name}
                    className={`${styles.stackTag} ${
                      categoryClass[tag.category]
                    }`}
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div className={styles.stackLegend}>
          <span
            className={`${styles.stackLegendItem} ${styles.stackLegendLanguage}`}
          >
            <span className={styles.stackLegendSwatch} />
            Language
          </span>
          <span
            className={`${styles.stackLegendItem} ${styles.stackLegendFramework}`}
          >
            <span className={styles.stackLegendSwatch} />
            Framework
          </span>
          <span
            className={`${styles.stackLegendItem} ${styles.stackLegendPlatform}`}
          >
            <span className={styles.stackLegendSwatch} />
            Platform
          </span>
        </div>
      </div>
    </section>
  );
}

function Philosophy(): ReactNode {
  const tenets = [
    {
      title: 'Agents need constraints, not freedom.',
      desc: "An unconstrained agent skips tests, makes sweeping changes, and produces code that works in isolation but breaks in context. The TDD guard exists because freedom doesn't scale.",
    },
    {
      title: 'Tests are the specs and the documentation.',
      desc: "Every test has a descriptive name. Test failures are the only time agents need to know what is in the test suite - no context pollution except when there's something to fix. And tests' contents tell your agent how things were meant to work.",
    },
    {
      title: 'Advanced linting you create, in code.',
      desc: "Write a Python script that walks your codebase's AST or checks code with regex. In fact, write lots of them. Go wild, because everything you codify reduces time spent explaining things to amnesiac agents and takes you out of one more loop. Every script means less things to tell your agent, more of your time spent sipping coffee, and better results by the time it stops working.",
    },
    {
      title: 'Monorepo for maximum productivity.',
      desc: 'Backend, frontend, database, migrations, lint rules, tests, CI, scripts and tools all happily coexisting in one repo. Changes that cross boundaries are normal, not exceptional. Plenty of documentation helps your agent work effectively with the patterns. Technologies such as Vite and patterns such as initial_data, carefully chosen for a fast, static frontend which is served with all data needed to hydrate it.',
    },
  ];

  return (
    <section className={styles.philosophy}>
      <div className={styles.container}>
        <div className={styles.philosophyGrid}>
          <div>
            <h2 className={styles.philosophyHeading}>
              Why
              <br />
              guardrails?
            </h2>
          </div>
          <div>
            {tenets.map(t => (
              <div key={t.title} className={styles.tenet}>
                <strong className={styles.tenetTitle}>{t.title}</strong>
                <p className={styles.tenetDesc}>{t.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function Home(): ReactNode {
  return (
    <Layout
      title="Your coding agent, on a leash"
      description="An opinionated, full stack framework & toolkit for high quality software development using Claude Code. Test-Driven Development process enforcement, architectural constraints, and code quality automation."
    >
      <div className={styles.page}>
        <Hero />
        <StateStrip />
        <LeashComparison />
        <Features />
        <Quickstart />
        <TechStack />
        <Philosophy />
      </div>
    </Layout>
  );
}
