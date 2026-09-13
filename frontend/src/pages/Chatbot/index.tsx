import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, RotateCcw, AlertTriangle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { ChatThread } from '../../components/domain/ChatThread';
import { ChatInput } from '../../components/domain/ChatInput';
import { useChatStore } from '../../store/chatStore';
import { useDocumentStore } from '../../store/documentStore';
import { documentService } from '../../services/api';

export const ChatbotPage: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { activeDocument } = useDocumentStore();
  const {
    messagesByDoc,
    isLoadingByDoc,
    isSendingByDoc,
    errorByDoc,
    initSession,
    sendMessage,
    clearChat,
  } = useChatStore();

  const [documentTitle, setDocumentTitle] = useState<string>('Document');
  const [initError, setInitError] = useState<string | null>(null);

  const documentId = id || '';
  const messages = (documentId && messagesByDoc[documentId]) || [];
  const isLoading = Boolean(documentId && isLoadingByDoc[documentId]);
  const isSending = Boolean(documentId && isSendingByDoc[documentId]);
  const sessionError = documentId ? errorByDoc[documentId] : null;

  // Initialize session and verify document status
  const initializeChat = useCallback(async () => {
    if (!documentId) return;

    try {
      // 1. Verify document completion
      let doc = activeDocument;
      if (!doc || doc.id !== documentId) {
        doc = await documentService.getById(documentId);
      }

      if (doc.status !== 'complete') {
        navigate(`/documents/${documentId}/processing`, { replace: true });
        return;
      }

      setDocumentTitle(doc.original_filename || `Document ${documentId}`);

      // 2. Initialize chat session & history
      await initSession(documentId);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to connect to chat';
      setInitError(msg);
    }
  }, [documentId, activeDocument, initSession, navigate]);

  useEffect(() => {
    initializeChat();
  }, [initializeChat]);

  const handleSendMessage = (messageText: string) => {
    if (!documentId) return;
    sendMessage(documentId, messageText);
  };

  const handleClearChat = () => {
    if (!documentId) return;
    clearChat(documentId);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-5 pb-10" data-testid="chatbot-page">
      {/* Breadcrumb Navigation */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-2 text-xs text-secondary-500">
        <Link to="/dashboard" className="hover:text-primary-700 hover:underline">
          Dashboard
        </Link>
        <span className="text-secondary-400">/</span>
        <Link to={`/documents/${documentId}`} className="hover:text-primary-700 hover:underline">
          Document Analysis
        </Link>
        <span className="text-secondary-400">/</span>
        <span className="text-secondary-900 font-semibold" aria-current="page">
          Document Assistant
        </span>
      </nav>

      {/* Page Header with Persistent Title for Routing Contract */}
      <header className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-secondary-200">
        <div className="space-y-1">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="info" size="sm">Grounded Q&amp;A</Badge>
            <span className="text-xs text-secondary-500 font-mono">Doc: {documentId}</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-primary-950">
            {t('chat.title', 'Document Assistant')}
          </h1>
          <p className="text-xs sm:text-sm text-secondary-600 truncate max-w-xl">
            {documentTitle}
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {messages.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleClearChat}
              className="gap-1.5 text-xs text-secondary-600 hover:text-red-700"
              aria-label="Clear chat history"
            >
              <RotateCcw className="w-3.5 h-3.5" aria-hidden="true" />
              <span>Clear Thread</span>
            </Button>
          )}

          <Link to={`/documents/${documentId}`}>
            <Button variant="secondary" size="sm" className="gap-1.5 text-xs font-medium">
              <ArrowLeft className="w-4 h-4" aria-hidden="true" />
              <span>{t('clauseDetail.backToAnalysis', 'Back to Analysis')}</span>
            </Button>
          </Link>
        </div>
      </header>

      {/* Persistent Legal Grounding Disclaimer Banner */}
      <div
        role="region"
        aria-label="Contract Grounding Notice"
        className="p-3 bg-secondary-50 border border-secondary-200 rounded-lg flex items-center gap-2.5 text-xs text-secondary-700"
      >
        <Shield className="w-4 h-4 text-primary-600 shrink-0" aria-hidden="true" />
        <span className="leading-relaxed">
          <strong className="font-semibold text-secondary-900">Document Grounding:</strong> Answers are strictly constrained to clauses in this uploaded contract. ClarifAI will explicitly refuse to answer if sufficient contractual context is not found.
        </span>
      </div>

      {/* Main Chat Container */}
      <Card elevation="md" className="flex flex-col h-[620px] overflow-hidden border-secondary-300">
        {/* Persistent Subtitle CardHeader for Routing Contract */}
        <CardHeader className="py-3 px-5 sm:px-6 border-b border-secondary-200 bg-secondary-50/60">
          <CardTitle className="text-sm font-semibold text-secondary-800 flex items-center justify-between">
            <span>Contract-Grounded Conversation</span>
            <span className="text-[11px] font-normal text-secondary-500 font-mono">
              Session Active
            </span>
          </CardTitle>
          <CardDescription className="text-xs text-secondary-500">
            Responses cite exact source clauses with direct inspection links.
          </CardDescription>
        </CardHeader>

        {/* Error Notification if initialization or session failed */}
        {(initError || sessionError) && (
          <div className="p-4 bg-red-50 border-b border-red-200 text-xs text-red-800 flex items-center justify-between" role="alert">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{initError || sessionError}</span>
            </div>
            <Button variant="outline" size="sm" onClick={initializeChat}>
              Retry
            </Button>
          </div>
        )}

        {/* Scrollable Conversation Thread */}
        <ChatThread
          documentId={documentId}
          messages={messages}
          isSending={isSending}
          onSelectQuestion={handleSendMessage}
        />

        {/* Pinned Query Input */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={isSending || isLoading}
          placeholder="Ask a question about this contract's clauses..."
        />
      </Card>
    </div>
  );
};
