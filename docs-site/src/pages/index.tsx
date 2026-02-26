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
            An opinionated full-stack scaffold with strong guardrails for
            AI-assisted development. TDD enforcement, architectural constraints,
            and code quality automation — because good constraints produce good
            code.
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
            <h3 className={styles.leashHeadingBad}>
              Your coding agent without a leash
            </h3>
            <div className={styles.leashImageWrap}>
              <img
                src="/img/leash-dont-walk.jpg"
                alt="Frustrated person telling their dog not to walk on the road - the dog ignores them"
                className={styles.leashImage}
              />
            </div>
          </div>
          <div className={styles.leashCard}>
            <h3 className={styles.leashHeadingGood}>
              Your coding agent on a leash
            </h3>
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
          We are in a time of change! Claude Code writes all code for my
          product,{' '}
          <a href="https://approviq.com" target="_blank" rel="noreferrer">
            ApprovIQ
          </a>{' '}
          - but it doesn't do it alone.
        </p>
        <p className={styles.leashDesc}>
          (And no, that wasn't an em-dash just now.)
        </p>
        <p className={styles.leashDesc}>
          Anyway. Agents go off the rails and get distracted. Asking nicely
          doesn&apos;t work. CodeLeash puts guardrails <em>outside</em> the
          agent, so it <em>can&apos;t</em> go off the rails. While everyone else
          is building the tallest tower of agent orchestration they can build,
          I've been tightly controlling outcomes by sharply defining what
          quality code looks like, and getting results. CodeLeash enforces
          quality with code based hooks, scripts, tools, and loops, in a way the
          agent can&apos;t ignore or bypass.
        </p>
        <p className={styles.leashDesc}>
          We don&apos;t ask agents nicely, we let them fail, then tell them how
          to correct it. That&apos;s why I&apos;ve used the analogy of a leash.
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
                  The agent MUST use TDD. A state machine enforces the
                  Red-Green-Refactor cycle and blocks file edits until tests
                  fail first. No shortcuts, no skipping ahead.
                </p>
                <p className={styles.featureCardDesc}>
                  A test suite in which the agent has seen every test fail -
                  then made each test pass by writing code - helps prevent
                  regressions and keeps development velocity high as your
                  product grows. Per-agent isolation lets agents run in parallel
                  without interfering.
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
                  regexes. Most code review feedback can be at least partly
                  automated. By the time your agent stops working, basic issues
                  were already fixed - and you know because the checks passed.
                  Never repeat obvious fixes again.
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

          <Link to="/docs/how-tests-work" className={styles.featureCardLink}>
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
                <h3 className={styles.featureCardTitle}>Strict Timeouts</h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  Each unit test must complete within 10ms. This forces pure
                  business logic - no I/O, no accidental imports, no framework
                  startup. If a test touches the network or spins up a server,
                  it fails.
                </p>
                <p className={styles.featureCardDesc}>
                  Auto-retry handles transient performance hiccups like JIT
                  warmup. When a test does time out, a flamegraph SVG is
                  generated automatically so you can see exactly where the time
                  went.
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

          <Link to="/docs/worker-system" className={styles.featureCardLink}>
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
                    <rect
                      x="4"
                      y="10"
                      width="28"
                      height="18"
                      rx="2"
                      stroke="rgb(160 100 50)"
                      strokeWidth="2"
                      fill="none"
                    />
                    <path
                      d="M4 16H32"
                      stroke="rgb(160 100 50)"
                      strokeWidth="2"
                    />
                    <circle cx="9" cy="13" r="1.5" fill="rgb(239 68 68)" />
                    <circle cx="14" cy="13" r="1.5" fill="rgb(234 179 8)" />
                    <circle cx="19" cy="13" r="1.5" fill="rgb(34 197 94)" />
                  </svg>
                </div>
                <h3 className={styles.featureCardTitle}>Worker System</h3>
              </div>
              <div className={styles.featureRight}>
                <p className={styles.featureCardDesc}>
                  A job queue system that only uses one database table and zero
                  external dependencies. No Redis, no RabbitMQ, no external
                  broker of any kind.
                </p>
                <p className={styles.featureCardDesc}>
                  Workers query the jobs table using SELECT FOR UPDATE SKIP
                  LOCKED. When done in a transaction the selected rows are
                  locked, and rows that were already locked are skipped over.
                </p>
                <p className={styles.featureCardDesc}>
                  Workers always pick up the next available job. When a worker
                  has finished (or crashes) the transaction is committed or
                  rolled back, either completing the job, or releasing it to be
                  retried.
                </p>
                <p className={styles.featureCardDesc}>
                  Ensures safe concurrent processing. Includes exponential
                  backoff retries, handler registration, and hot reload in
                  development.
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
                <h3 className={styles.featureCardTitle}>Worktree Isolation</h3>
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
              className={`${styles.featureCard} ${styles.featureCardReversed} ${styles.featureCardGreen}`}
            >
              <div className={styles.featureLeft}>
                <span
                  className={`${styles.featureNumber} ${styles.featureNumberGreen}`}
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
                  Full-Stack Integration
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
                  className={`${styles.featureLearnMore} ${styles.featureLearnMoreGreen}`}
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
              Vite, FastAPI, and the worker with hot reload.
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
      description="An opinionated full-stack scaffold with strong guardrails for AI-assisted development. TDD enforcement, architectural constraints, and code quality automation."
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
