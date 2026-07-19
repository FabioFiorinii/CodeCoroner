# CodeCoroner — Frontend Design

## Tech Stack

- **Framework**: React 18 + TypeScript 5
- **Build**: Vite 5
- **Routing**: React Router v6
- **State**: Zustand (client state) + TanStack Query / React Query (server state)
- **UI**: Tailwind CSS 4 + shadcn/ui component library
- **HTTP**: Axios + @tanstack/react-query
- **WebSocket**: useWebSocket (reconnecting)
- **Charts**: recharts (metrics)
- **Diff Viewer**: react-diff-viewer-continued
- **Markdown**: react-markdown + rehype-highlight

## Pages & Routes

```
/login                          → LoginPage
/register                       → RegisterPage
/dashboard                      → DashboardPage (protected)
/projects                       → ProjectListPage
/projects/new                   → ProjectCreatePage
/projects/:id                   → ProjectDetailPage
/projects/:id/settings          → ProjectSettingsPage
/projects/:id/repositories      → RepoListPage
/projects/:id/repositories/:rid → RepoDetailPage
/analyses                       → AnalysisListPage
/analyses/:id                   → AnalysisDetailPage
/analyses/:id/localization      → BugLocalizationPage
/analyses/:id/root-cause        → RootCausePage
/analyses/:id/patch             → PatchPage (V1)
/analyses/:id/report            → ReportPage
/settings                       → UserSettingsPage
```

## Component Tree

```
App
├── Layout
│   ├── Sidebar
│   │   ├── Logo
│   │   ├── NavItems
│   │   │   ├── DashboardLink
│   │   │   ├── ProjectsLink
│   │   │   ├── AnalysesLink
│   │   │   └── SettingsLink
│   │   └── UserMenu
│   ├── TopBar
│   │   ├── Breadcrumbs
│   │   ├── SearchInput (global search)
│   │   └── NotificationBell
│   └── MainContent (Outlet)
│
├── DashboardPage
│   ├── StatsCards
│   │   ├── TotalAnalysesCard
│   │   ├── SuccessRateCard
│   │   ├── AvgDurationCard
│   │   └── ActiveProjectsCard
│   ├── RecentAnalysesTable
│   └── ActivityChart (last 30 days)
│
├── ProjectListPage
│   ├── ProjectFilters (status, search)
│   └── ProjectCard[]
│       ├── ProjectName
│       ├── RepoCount
│       ├── LastActivity
│       └── ActionsMenu
│
├── ProjectCreatePage
│   └── ProjectForm
│       ├── NameField
│       ├── DescriptionField
│       └── SubmitButton
│
├── ProjectDetailPage
│   ├── ProjectHeader
│   ├── Tabs
│   │   ├── RepositoriesTab
│   │   │   ├── AddRepoForm (git URL + branch)
│   │   │   └── RepoTable
│   │   │       ├── RepoRow (status badge, file count, actions)
│   │   │       └── IndexProgress (inline status)
│   │   ├── MembersTab
│   │   │   ├── MemberList
│   │   │   └── AddMemberForm
│   │   └── AnalysesTab (recent analyses for project)
│   └── ProjectActions
│
├── AnalysisListPage
│   ├── AnalysisFilters
│   │   ├── StatusFilter
│   │   ├── ProjectFilter
│   │   ├── DateRangeFilter
│   │   └── SearchInput
│   └── AnalysisTable
│       ├── AnalysisRow
│       │   ├── Title
│       │   ├── Project
│       │   ├── StatusBadge
│       │   ├── Duration
│       │   └── CreatedAt
│       └── Pagination
│
├── AnalysisDetailPage
│   ├── AnalysisHeader
│   │   ├── Title
│   │   ├── StatusTimeline
│   │   │   └── StepIndicator[]
│   │   │       ├── StepIcon (pending/running/done/failed)
│   │   │       └── StepLabel
│   │   └── Duration
│   ├── ErrorContextCard
│   │   ├── StacktraceView (syntax highlighted)
│   │   ├── LogView
│   │   └── DescriptionView
│   ├── ResultTabs
│   │   ├── LocalizationTab → BugLocalizationPage
│   │   ├── RootCauseTab   → RootCausePage
│   │   ├── PatchTab       → PatchPage (V1)
│   │   └── ReportTab      → ReportPage
│   └── AnalysisActions (re-run, export)
│
├── BugLocalizationPage
│   ├── SummaryCard
│   ├── SuspicionChart (horizontal bar chart)
│   │   └── SuspicionBar[]
│   │       ├── FilePath (clickable → opens code)
│   │       ├── ScoreBadge
│   │       └── MatchedLines
│   ├── FileDetailPanel (slideover)
│   │   ├── FilePath
│   │   ├── CodeViewer (syntax highlighted, line numbers)
│   │   │   └── HighlightedLines (matched lines emphasized)
│   │   └── EvidenceSnippets
│   └── ExportButton
│
├── RootCausePage
│   ├── RCAHeader
│   │   ├── RootFile (link to code)
│   │   ├── RootLineNumber
│   │   ├── ConfidenceBadge
│   │   └── SummaryText
│   ├── CauseChainCard
│   │   └── CauseChainFlow (visual chain of events)
│   │       ├── CauseNode[]
│   │       └── ArrowConnector
│   ├── ReasoningCard
│   │   └── MarkdownContent (full reasoning)
│   └── EvidenceLinks (chunks used)
│
├── PatchPage (V1)
│   ├── PatchHeader
│   │   ├── StatusBadge
│   │   ├── ValidationScore
│   │   └── Summary
│   ├── DiffViewer
│   │   └── DiffFile[]
│   │       ├── FileHeader
│   │       └── DiffLines (highlighted)
│   ├── ValidationResults
│   │   ├── TestResultsRow (passed/failed/skipped)
│   │   ├── LintResultsRow (errors/warnings)
│   │   └── TypeCheckRow
│   └── PatchActions (apply, reject, download)
│
├── ReportPage
│   ├── ReportHeader
│   ├── ReportTabs (markdown preview / raw)
│   ├── ReportMarkdown (rendered)
│   └── ExportOptions (PDF, HTML, Markdown)
│
└── UserSettingsPage
    ├── ProfileSection
    ├── ApiTokensSection
    │   ├── TokenList
    │   └── GenerateTokenForm
    └── PreferencesSection
```

## State Management

```typescript
// Zustand stores
interface AuthStore {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isLoading: boolean;
}

interface AnalysisStore {
  currentAnalysis: Analysis | null;
  statusStream: WebSocket | null;
  connectStatusStream: (analysisId: string) => void;
  disconnectStatusStream: () => void;
}

// TanStack Query keys
const queryKeys = {
  projects: {
    all: ['projects'] as const,
    detail: (id: string) => ['projects', id] as const,
    members: (id: string) => ['projects', id, 'members'] as const,
  },
  repositories: {
    all: (projectId: string) => ['repositories', projectId] as const,
    detail: (id: string) => ['repositories', id] as const,
    files: (id: string) => ['repositories', id, 'files'] as const,
    chunks: (id: string) => ['repositories', id, 'chunks'] as const,
  },
  analyses: {
    all: (filters?: AnalysisFilters) => ['analyses', filters] as const,
    detail: (id: string) => ['analyses', id] as const,
    localization: (id: string) => ['analyses', id, 'localization'] as const,
    rootCause: (id: string) => ['analyses', id, 'rootCause'] as const,
    patch: (id: string) => ['analyses', id, 'patch'] as const,
    report: (id: string) => ['analyses', id, 'report'] as const,
  },
} as const;
```

## Key TypeScript Types

```typescript
// Domain types
interface Project {
  id: string;
  name: string;
  description: string;
  createdBy: string;
  createdAt: string;
  memberCount: number;
  repoCount: number;
}

interface Repository {
  id: string;
  projectId: string;
  gitUrl: string;
  gitBranch: string;
  status: 'pending' | 'cloning' | 'indexing' | 'indexed' | 'error';
  fileCount: number;
  lastIndexedAt: string | null;
}

interface Analysis {
  id: string;
  projectId: string;
  repositoryId: string;
  title: string;
  status: AnalysisStatus;
  errorContext: ErrorContext;
  createdAt: string;
  completedAt: string | null;
  durationSeconds: number | null;
}

type AnalysisStatus =
  | 'queued' | 'indexing' | 'analyzing'
  | 'bug_localization' | 'rca'
  | 'patching' | 'validating'
  | 'completed' | 'failed';

interface ErrorContext {
  stacktrace?: string;
  logs?: string;
  error_message?: string;
  description?: string;
  environment?: string;
  steps_to_reproduce?: string;
}

interface SuspiciousFile {
  filePath: string;
  suspicionScore: number;
  matchedLines: number[];
  evidence: string;
  rank: number;
}

interface BugLocalization {
  summary: string;
  suspiciousFiles: SuspiciousFile[];
}

interface RootCause {
  summary: string;
  rootFile: string;
  rootLine: number | null;
  causeChain: string;
  confidence: number;
  reasoning: string;
}

interface Patch {
  id: string;
  diff: string;
  summary: string;
  status: 'pending' | 'applied' | 'validated' | 'rejected';
  validation?: PatchValidation;
}

interface PatchValidation {
  testsPassed: number;
  testsFailed: number;
  lintErrors: number;
  typeErrors: number;
  overallScore: number;
}

interface Report {
  markdown: string;
  format: 'markdown' | 'pdf' | 'html';
}

// UI State
interface StatusStep {
  label: string;
  key: AnalysisStatus;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number; // 0-100
}
```

## UI Flow: Analysis Submission

```
User clicks "New Analysis"
  → Modal/Page with form:
    ├── Select Project (dropdown)
    ├── Select Repository (dropdown, filtered by project)
    ├── Title (optional)
    ├── Error Context sections:
    │   ├── Stacktrace (textarea, monospace)
    │   ├── Logs (textarea, monospace)
    │   ├── Error Message (input)
    │   ├── Description (textarea)
    │   ├── Environment (input)
    │   └── Steps to Reproduce (textarea)
    └── Submit button

On submit:
  → POST /api/v1/analyses/ → receives analysis ID
  → Navigate to /analyses/:id
  → Establish WebSocket to /ws/analyses/{id}
  → Show StatusTimeline with live updates
  → Each step transitions: pending → running → completed
  → On completion: enable tabs for results
```

## UI Flow: Status Timeline Component

```
┌──────────────────────────────────────────────────────────┐
│ Analysis Status  ● ● ● ● ● ● ● ● ●                    │
│                   1  2  3  4  5  6  7  8  9              │
│                                                          │
│  ●━━━━━━━━━━━━━━━━━━━                                  │
│ 1. Indexing          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  100%        │
│ 2. Analyzing         ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  100%        │
│ 3. Bug Localization  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░   80%        │
│ 4. Root Cause        ░░░░░░░░░░░░░░░░░░░░░    0%        │
│ 5. Report            ░░░░░░░░░░░░░░░░░░░░░    0%        │
└──────────────────────────────────────────────────────────┘
```
