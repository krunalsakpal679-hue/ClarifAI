/* eslint-disable react-refresh/only-export-components */
import { createBrowserRouter, type RouteObject } from 'react-router-dom';
import { AppShell } from '../layouts/AppShell';
import { AuthLayout } from '../layouts/AuthLayout';
import { ProtectedLayout } from '../layouts/ProtectedLayout';

import {
  LandingPage,
  LoginPage,
  SignupPage,
  DashboardPage,
  HistoryPage,
  UploadPage,
  ProcessingPage,
  AnalysisResultsPage,
  ClauseDetailPage,
  ChatbotPage,
  ComparisonSetupPage,
  ComparisonResultsPage,
  SettingsPage,
  NotFoundPage,
} from '../pages';

/**
 * Route path constants providing type-safe path resolution.
 */
export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  DASHBOARD: '/dashboard',
  HISTORY: '/history',
  UPLOAD: '/upload',
  PROCESSING: (id: string) => `/documents/${id}/processing`,
  ANALYSIS: (id: string) => `/documents/${id}`,
  CLAUSE_DETAIL: (id: string, clauseId: string) => `/documents/${id}/clauses/${clauseId}`,
  CHATBOT: (id: string) => `/documents/${id}/chat`,
  COMPARE: '/compare',
  COMPARE_RESULTS: (idA: string, idB: string) => `/compare/${idA}/${idB}`,
  SETTINGS: '/settings',
} as const;

export const routes: RouteObject[] = [
  // Auth Layout Routes (Split-screen auth)
  {
    element: <AuthLayout />,
    children: [
      {
        path: '/login',
        element: <LoginPage />,
      },
      {
        path: '/signup',
        element: <SignupPage />,
      },
    ],
  },

  // Main AppShell Routes (with nav bar, skip-link, and persistent legal disclaimer)
  {
    element: <AppShell />,
    children: [
      // Public Landing Route
      {
        path: '/',
        element: <LandingPage />,
      },

      // Authenticated Protected Routes
      {
        element: <ProtectedLayout />,
        children: [
          {
            path: '/dashboard',
            element: <DashboardPage />,
          },
          {
            path: '/history',
            element: <HistoryPage />,
          },
          {
            path: '/upload',
            element: <UploadPage />,
          },
          {
            path: '/documents/:id/processing',
            element: <ProcessingPage />,
          },
          {
            path: '/documents/:id',
            element: <AnalysisResultsPage />,
          },
          {
            path: '/documents/:id/clauses/:clauseId',
            element: <ClauseDetailPage />,
          },
          {
            path: '/documents/:id/chat',
            element: <ChatbotPage />,
          },
          {
            path: '/compare',
            element: <ComparisonSetupPage />,
          },
          {
            path: '/compare/:idA/:idB',
            element: <ComparisonResultsPage />,
          },
          {
            path: '/compare/:comparisonId',
            element: <ComparisonResultsPage />,
          },
          {
            path: '/settings',
            element: <SettingsPage />,
          },
        ],
      },

      // 404 Catch-All Route
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
];

export const router = createBrowserRouter(routes);
