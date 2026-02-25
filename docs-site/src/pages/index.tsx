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
              GitHub
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
        <span className={`${styles.stateNode} ${styles.stateNodeActive}`}>
          initial
        </span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateLabel}>log red</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateNode}>red_intent</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateLabel}>test fails</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={`${styles.stateNode} ${styles.stateNodeRed}`}>
          red
        </span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateLabel}>log green</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={`${styles.stateNode} ${styles.stateNodeGreen}`}>
          green_intent
        </span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={styles.stateLabel}>tests pass</span>
        <span className={styles.stateArrow}>&rarr;</span>
        <span className={`${styles.stateNode} ${styles.stateNodeActive}`}>
          initial
        </span>
      </div>
    </div>
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
          <div className={styles.featureCard}>
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
            <h3 className={styles.featureCardTitle}>TDD Guard</h3>
            <p className={styles.featureCardDesc}>
              State machine forces Red-Green-Refactor cycle. Blocks file edits
              until tests fail first. Per-agent isolation via transcript-hashed
              log files.
            </p>
            <span className={styles.featureTag}>hooks + state machine</span>
          </div>

          <div className={styles.featureCard}>
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
                  stroke="rgb(59 130 246)"
                  strokeWidth="2"
                  fill="none"
                />
                <path
                  d="M18 10V18L23 23"
                  stroke="rgb(59 130 246)"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <h3 className={styles.featureCardTitle}>10ms Timeout</h3>
            <p className={styles.featureCardDesc}>
              Unit tests enforce a 10ms limit. Forces pure business logic — no
              I/O, no accidental imports. Auto-retry for transients, flamegraph
              SVG on failure.
            </p>
            <span className={styles.featureTag}>pytest hook</span>
          </div>

          <div className={styles.featureCard}>
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
            <p className={styles.featureCardDesc}>
              Custom Python scripts walking ASTs, running as pre-commit hooks.
              Brand colors, unused routes, soft deletes, dynamic imports, and
              more.
            </p>
            <span className={styles.featureTag}>ast + pre-commit</span>
          </div>

          <div className={styles.featureCard}>
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
                  stroke="rgb(59 130 246)"
                  strokeWidth="2"
                  fill="none"
                />
                <path d="M4 16H32" stroke="rgb(59 130 246)" strokeWidth="2" />
                <circle cx="9" cy="13" r="1.5" fill="rgb(239 68 68)" />
                <circle cx="14" cy="13" r="1.5" fill="rgb(234 179 8)" />
                <circle cx="19" cy="13" r="1.5" fill="rgb(34 197 94)" />
              </svg>
            </div>
            <h3 className={styles.featureCardTitle}>Worker System</h3>
            <p className={styles.featureCardDesc}>
              PostgreSQL job queue using FOR UPDATE SKIP LOCKED. Exponential
              backoff retries, handler registration, hot reload in dev. No
              external broker.
            </p>
            <span className={styles.featureTag}>postgresql + asyncio</span>
          </div>

          <div className={styles.featureCard}>
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
                <path d="M14 8V28" stroke="rgb(224 224 224)" strokeWidth="1" />
                <path d="M20 8V28" stroke="rgb(224 224 224)" strokeWidth="1" />
                <path d="M26 8V28" stroke="rgb(224 224 224)" strokeWidth="1" />
                <path d="M8 14H28" stroke="rgb(224 224 224)" strokeWidth="1" />
                <path d="M8 20H28" stroke="rgb(224 224 224)" strokeWidth="1" />
                <circle cx="14" cy="14" r="3" fill="rgb(59 130 246)" />
                <circle cx="20" cy="20" r="3" fill="rgb(34 197 94)" />
                <circle cx="26" cy="14" r="3" fill="rgb(239 68 68)" />
              </svg>
            </div>
            <h3 className={styles.featureCardTitle}>Worktree Isolation</h3>
            <p className={styles.featureCardDesc}>
              Parallel development with deterministic port hashing. Each git
              worktree gets its own FastAPI port, Vite port, and Supabase
              instance.
            </p>
            <span className={styles.featureTag}>init.sh + cksum</span>
          </div>

          <div className={styles.featureCard}>
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
                  stroke="rgb(59 130 246)"
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
            <h3 className={styles.featureCardTitle}>Full-Stack Integration</h3>
            <p className={styles.featureCardDesc}>
              Vite + FastAPI + React with a server-to-client initial data
              bridge. render_page() &rarr; data-initial &rarr; useInitialData().
              Type-safe from Pydantic to TypeScript.
            </p>
            <span className={styles.featureTag}>vite + fastapi + react</span>
          </div>
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
              Two commands.
              <br />
              <em className={styles.quickstartAccent}>That's it.</em>
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
  const highlighted = ['Python', 'FastAPI', 'React', 'TypeScript'];
  const normal = [
    'Supabase',
    'Vite',
    'Tailwind CSS',
    'Playwright',
    'Prometheus',
    'OpenTelemetry',
  ];

  return (
    <section className={styles.stack}>
      <div className={styles.container}>
        <div className={styles.sectionHeader}>
          <span className={styles.sectionNumber}>02</span>
          <span className={styles.sectionTitle}>Stack</span>
        </div>
        <div className={styles.stackFlex}>
          {highlighted.map(tag => (
            <span
              key={tag}
              className={`${styles.stackTag} ${styles.stackTagHighlight}`}
            >
              {tag}
            </span>
          ))}
          {normal.map(tag => (
            <span key={tag} className={styles.stackTag}>
              {tag}
            </span>
          ))}
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
      title: 'Tests are the specification.',
      desc: "The 10ms timeout forces unit tests to be pure logic. The e2e harness ensures full integration. The pre-commit hook runs everything. If it isn't tested, it doesn't exist.",
    },
    {
      title: 'Lint rules should be code.',
      desc: 'Instead of configuring complex YAML, write a Python script that walks an AST. A script is easier to write, debug, and explain than a configuration.',
    },
    {
      title: 'The monorepo is the product.',
      desc: 'Backend, frontend, database migrations, lint rules, tests, and CI all live together. Changes that cross boundaries are normal, not exceptional.',
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
        <Features />
        <Quickstart />
        <TechStack />
        <Philosophy />
      </div>
    </Layout>
  );
}
