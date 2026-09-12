import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { routes } from '../../../app/router';
import { useAuthStore } from '../../../store/authStore';
import { useChatStore } from '../../../store/chatStore';
import { useDocumentStore } from '../../../store/documentStore';
import { __resetMockChat, __setMockChatHistory } from '../../../services/mocks/chat';
import { __resetMockDocuments, __setMockDocumentStatus } from '../../../services/mocks/documents';

const mockUser = {
  id: 'usr_counsel',
  email: 'counsel@clarifai.internal',
  fullName: 'Jane Counsel',
  preferredLanguage: 'en' as const,
  createdAt: '2026-09-12T00:00:00.000Z',
};

describe('ChatbotPage (PRD Ch. 17, 22.9 & Section 8.4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    __resetMockDocuments();
    __resetMockChat();
    useAuthStore.getState().setAuth(mockUser, 'valid_token');
    useDocumentStore.getState().reset();
    useChatStore.getState().reset();
  });

  const renderRoute = (initialPath: string) => {
    const memoryRouter = createMemoryRouter(routes, {
      initialEntries: [initialPath],
    });
    return render(<RouterProvider router={memoryRouter} />);
  };

  it('renders page header, grounding notice, and existing conversation history', async () => {
    renderRoute('/documents/doc-msa-001/chat');

    // Header and routing contract assertions
    expect(screen.getByRole('heading', { name: /Document Assistant/i })).toBeInTheDocument();
    expect(screen.getByText(/Contract-Grounded Conversation/i)).toBeInTheDocument();

    // Persistent grounding notice
    expect(
      screen.getByRole('region', { name: /Contract Grounding Notice/i })
    ).toBeInTheDocument();

    // Wait for history to load
    await waitFor(() => {
      expect(
        screen.getByText(/What are the payment terms in this agreement/i)
      ).toBeInTheDocument();
    });

    // Verify assistant grounded answer and citation link
    expect(screen.getByText(/Invoices are due within fifteen/i)).toBeInTheDocument();
    expect(screen.getByTestId('source-clause-link-clause-104')).toBeInTheDocument();
  });

  it('renders suggested question chips in empty conversation state and sends question on click', async () => {
    // Empty message history
    __setMockChatHistory('doc-msa-001', []);

    renderRoute('/documents/doc-msa-001/chat');

    await waitFor(() => {
      expect(screen.getByTestId('chat-empty-state')).toBeInTheDocument();
    });

    const chip = screen.getByRole('button', {
      name: /Can the vendor terminate this agreement without cause/i,
    });
    expect(chip).toBeInTheDocument();

    // Click suggested chip
    fireEvent.click(chip);

    // Wait for user message and grounded response
    await waitFor(
      () => {
        expect(
          screen.getByText(/Can the vendor terminate this agreement without cause/i)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    await waitFor(
      () => {
        expect(
          screen.getByText(/Section 18.1 grants the vendor the right to terminate immediately/i)
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(screen.getByTestId('source-clause-link-clause-102')).toBeInTheDocument();
  });

  it('displays PRD Ch. 17.7 controlled no-answer response when query lacks document context', async () => {
    renderRoute('/documents/doc-msa-001/chat');

    await waitFor(() => {
      expect(screen.getByText(/What are the payment terms/i)).toBeInTheDocument();
    });

    const input = screen.getByRole('textbox', {
      name: /ask a question about this contract/i,
    });
    expect(screen.getByRole('button', { name: /send message/i })).toBeInTheDocument();

    fireEvent.change(input, {
      target: { value: 'What are the company travel meal allowances?' },
    });
    fireEvent.submit(screen.getByTestId('chat-input-form'));

    await waitFor(
      () => {
        expect(
          screen.getByText(
            "I couldn't find enough information in the uploaded document to answer this question reliably."
          )
        ).toBeInTheDocument();
      },
      { timeout: 3000 }
    );

    expect(screen.getByTestId('chat-message-no-answer')).toBeInTheDocument();
  });

  it('redirects to processing page when document is incomplete', async () => {
    __setMockDocumentStatus('doc-lease-005', 'segmenting');

    renderRoute('/documents/doc-lease-005/chat');

    await waitFor(() => {
      expect(screen.getByText(/Analyzing Document/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/doc-lease-005/i)).toBeInTheDocument();
  });

  it('clears chat thread when clear thread button is clicked', async () => {
    renderRoute('/documents/doc-msa-001/chat');

    await waitFor(() => {
      expect(screen.getByText(/What are the payment terms/i)).toBeInTheDocument();
    });

    const clearBtn = screen.getByRole('button', { name: /clear chat history/i });
    expect(clearBtn).toBeInTheDocument();

    fireEvent.click(clearBtn);

    await waitFor(() => {
      expect(screen.getByTestId('chat-empty-state')).toBeInTheDocument();
    });
  });
});
