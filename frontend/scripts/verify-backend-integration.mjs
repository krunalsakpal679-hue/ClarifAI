/**
 * ClarifAI Phase 15 Backend Integration & Contract Verification Script
 *
 * Verifies all Section 8 endpoints against the live running Django backend.
 */
import fs from 'fs';
import path from 'path';

const BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
console.log(`[Phase 15 Verification] Connecting to Backend at: ${BASE_URL}`);

let cookieJar = '';

function updateCookies(res) {
  const setCookie = res.headers.get('set-cookie');
  if (setCookie) {
    // Extract name=value pairs
    const parts = setCookie.split(',').map(s => s.trim());
    for (const part of parts) {
      const match = part.match(/^([^=;]+)=([^;]+)/);
      if (match) {
        const key = match[1].trim();
        const val = match[2].trim();
        if (key === 'refresh_token') {
          cookieJar = `${key}=${val}`;
        }
      }
    }
  }
}

async function request(endpoint, options = {}) {
  const headers = { ...options.headers };
  if (cookieJar) {
    headers['Cookie'] = cookieJar;
  }
  const url = `${BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers,
  });
  updateCookies(res);
  return res;
}

// Minimal valid PDF binary generator
function createMinimalPdfBuffer(title = "ClarifAI Test Legal Agreement") {
  const content = `%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>
endobj
4 0 obj
<< /Length 55 >>
stream
BT
/F1 12 Tf
72 712 Td
(${title}) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000214 00000 n 
trailer
<< /Size 5 /Root 1 0 R >>
startxref
318
%%EOF`;
  return Buffer.from(content, 'utf-8');
}

const results = [];
function record(step, passed, details = '') {
  results.push({ step, passed, details });
  const status = passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status}: ${step} ${details ? `(${details})` : ''}`);
  if (!passed) {
    throw new Error(`Integration step failed: ${step} - ${details}`);
  }
}

async function run() {
  console.log('\n--- 1. Health Check (Section 8) ---');
  const healthRes = await request('/api/health/');
  record('Health Check HTTP 200', healthRes.status === 200, `status: ${healthRes.status}`);
  const healthData = await healthRes.json();
  record('Health Check Service Name', healthData.service === 'ClarifAI Django API', healthData.service);

  console.log('\n--- 2. Authentication Flow (Section 8.1 & PRD Ch. 30.1) ---');
  const uniqueSuffix = Date.now();
  const testEmail = `integration_tester_${uniqueSuffix}@clarifai.internal`;
  const testPassword = 'SecurePassword123!';

  // Signup
  const signupRes = await request('/api/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: testEmail, password: testPassword }),
  });
  record('POST /api/auth/signup HTTP 201', signupRes.status === 201, `status: ${signupRes.status}`);
  const signupData = await signupRes.json();
  record('Signup returns user object', Boolean(signupData.user && signupData.user.id), signupData.user?.id);
  record('Signup returns access token', typeof signupData.access === 'string' && signupData.access.length > 20);
  record('Signup sets httpOnly refresh_token cookie', cookieJar.includes('refresh_token'));

  let accessToken = signupData.access;

  // Refresh
  const refreshRes = await request('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  });
  record('POST /api/auth/refresh HTTP 200', refreshRes.status === 200, `status: ${refreshRes.status}`);
  const refreshData = await refreshRes.json();
  record('Refresh returns new access token', typeof refreshData.access === 'string');
  accessToken = refreshData.access;

  // Logout
  const logoutRes = await request('/api/auth/logout', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
  });
  record('POST /api/auth/logout HTTP 200', logoutRes.status === 200, `status: ${logoutRes.status}`);

  // Login
  const loginRes = await request('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: testEmail, password: testPassword }),
  });
  record('POST /api/auth/login HTTP 200', loginRes.status === 200, `status: ${loginRes.status}`);
  const loginData = await loginRes.json();
  record('Login returns valid user and access token', Boolean(loginData.user && loginData.access));
  accessToken = loginData.access;

  console.log('\n--- 3. Authorization Boundaries (Section 8.2 & PRD Ch. 26.7) ---');
  const unauthRes = await request('/api/documents/');
  record('Unauthenticated request rejected with 401', unauthRes.status === 401, `status: ${unauthRes.status}`);
  const unauthError = await unauthRes.json();
  record('Standard error code AUTHENTICATION_FAILED', unauthError.error?.code === 'AUTHENTICATION_FAILED', unauthError.error?.code);

  console.log('\n--- 4. Document Upload & 9-Stage Processing (Section 8.2 & PRD Ch. 15) ---');
  const pdfBuffer1 = createMinimalPdfBuffer("Master Services Agreement - Alpha Corp");
  const formData1 = new FormData();
  formData1.append('file', new Blob([pdfBuffer1], { type: 'application/pdf' }), 'msa_alpha_corp.pdf');

  const uploadRes1 = await request('/api/documents/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${accessToken}` },
    body: formData1,
  });
  record('POST /api/documents/ HTTP 201', uploadRes1.status === 201, `status: ${uploadRes1.status}`);
  const uploadData1 = await uploadRes1.json();
  record('Upload response has id and filename', Boolean(uploadData1.id && uploadData1.original_filename), uploadData1.original_filename);
  const doc1Id = uploadData1.id;

  // Poll status
  let doc1Status = uploadData1.status;
  let attempts = 0;
  while (doc1Status !== 'complete' && doc1Status !== 'failed' && attempts < 20) {
    attempts++;
    await new Promise(r => setTimeout(r, 500));
    const pollRes = await request(`/api/documents/${doc1Id}/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` },
    });
    const pollData = await pollRes.json();
    doc1Status = pollData.status;
    console.log(`  Polling document ${doc1Id} status: ${doc1Status} (attempt ${attempts})`);
  }
  record('Document processing completed', doc1Status === 'complete', `status: ${doc1Status}`);

  // Fetch Summary
  console.log('\n--- 5. Document Summary & Translation (Section 8.3 & PRD Ch. 16, 19) ---');
  const summaryRes = await request(`/api/documents/${doc1Id}/summary/?lang=en`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/documents/{id}/summary/ HTTP 200', summaryRes.status === 200, `status: ${summaryRes.status}`);
  const summaryData = await summaryRes.json();
  record('Summary contains purpose_text', typeof summaryData.purpose_text === 'string' && summaryData.purpose_text.length > 0);
  record('Summary contains translation_available', typeof summaryData.translation_available === 'boolean');

  // Fetch Clauses
  console.log('\n--- 6. Clauses & Severity Badging (Section 8.3 & PRD Ch. 16, 22.8) ---');
  const clausesRes = await request(`/api/documents/${doc1Id}/clauses/?lang=en`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/documents/{id}/clauses/ HTTP 200', clausesRes.status === 200, `status: ${clausesRes.status}`);
  const clausesData = await clausesRes.json();
  record('Clauses returned in results array', Array.isArray(clausesData.results) && clausesData.results.length > 0, `count: ${clausesData.results.length}`);

  const firstClause = clausesData.results[0];
  record('Clause has original_text and simplified_text', Boolean(firstClause.original_text && firstClause.simplified_text));
  record('Clause has rule_findings array', Array.isArray(firstClause.rule_findings));

  // Single Clause Detail
  const clauseDetailRes = await request(`/api/documents/${doc1Id}/clauses/${firstClause.id}/`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/documents/{id}/clauses/{clause_id}/ HTTP 200', clauseDetailRes.status === 200, `status: ${clauseDetailRes.status}`);
  const clauseDetailData = await clauseDetailRes.json();
  record('Clause detail matches ID', clauseDetailData.id === firstClause.id);

  console.log('\n--- 7. Chatbot with Citations (Section 8.4 & PRD Ch. 17, 30.4) ---');
  const chatSessionRes = await request(`/api/documents/${doc1Id}/chat/sessions/`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/documents/{id}/chat/sessions/ HTTP 200', chatSessionRes.status === 200, `status: ${chatSessionRes.status}`);
  const chatSessionData = await chatSessionRes.json();
  record('Chat session created with title', Boolean(chatSessionData.id && chatSessionData.title));

  const chatMsgRes = await request(`/api/documents/${doc1Id}/chat/messages/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ message: "What are the liability limits in this contract?" }),
  });
  record('POST /api/documents/{id}/chat/messages/ HTTP 201', chatMsgRes.status === 201, `status: ${chatMsgRes.status}`);
  const chatMsgData = await chatMsgRes.json();
  record('Assistant response contains citations array', Array.isArray(chatMsgData.source_clause_ids), `citations: ${chatMsgData.source_clause_ids.length}`);
  record('Assistant response contains answer text', typeof chatMsgData.content === 'string' && chatMsgData.content.length > 0);

  const chatHistoryRes = await request(`/api/documents/${doc1Id}/chat/messages/`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/documents/{id}/chat/messages/ HTTP 200', chatHistoryRes.status === 200, `status: ${chatHistoryRes.status}`);

  console.log('\n--- 8. Contract Comparison Flow (Section 8.5 & PRD Ch. 18, 30.5) ---');
  // Upload second document
  const pdfBuffer2 = createMinimalPdfBuffer("Master Services Agreement - Beta Corp (Revised)");
  const formData2 = new FormData();
  formData2.append('file', new Blob([pdfBuffer2], { type: 'application/pdf' }), 'msa_beta_corp.pdf');

  const uploadRes2 = await request('/api/documents/', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${accessToken}` },
    body: formData2,
  });
  record('Upload Document B HTTP 201', uploadRes2.status === 201);
  const uploadData2 = await uploadRes2.json();
  const doc2Id = uploadData2.id;

  // Poll doc2
  let doc2Status = uploadData2.status;
  while (doc2Status !== 'complete' && doc2Status !== 'failed') {
    await new Promise(r => setTimeout(r, 500));
    const pollRes2 = await request(`/api/documents/${doc2Id}/`, {
      headers: { 'Authorization': `Bearer ${accessToken}` },
    });
    const pollData2 = await pollRes2.json();
    doc2Status = pollData2.status;
  }
  record('Document B processing complete', doc2Status === 'complete');

  // Initiate Comparison
  const compRes = await request('/api/comparisons/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ document_a_id: doc1Id, document_b_id: doc2Id }),
  });
  record('POST /api/comparisons/ HTTP 201', compRes.status === 201, `status: ${compRes.status}`);
  const compData = await compRes.json();
  record('Comparison created with results', Array.isArray(compData.results));

  // Get Comparison Detail
  const compDetailRes = await request(`/api/comparisons/${compData.id}/?lang=en`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/comparisons/{id}/ HTTP 200', compDetailRes.status === 200, `status: ${compDetailRes.status}`);

  console.log('\n--- 9. Report Generation & Streamed Download (Section 8.6 & PRD Ch. 21, 30.6) ---');
  const genReportRes = await request(`/api/documents/${doc1Id}/report/?lang=en`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ language: 'en' }),
  });
  record('POST /api/documents/{id}/report/ HTTP 201', genReportRes.status === 201, `status: ${genReportRes.status}`);
  const reportData = await genReportRes.json();
  const reportId = reportData.id || reportData.report_id;
  record('Report generated with ID and COMPLETE status', reportData.status === 'complete', `id: ${reportId}`);

  // Download PDF
  const downloadRes = await request(`/api/reports/${reportId}/download/`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/reports/{id}/download/ HTTP 200', downloadRes.status === 200, `status: ${downloadRes.status}`);
  const contentType = downloadRes.headers.get('content-type');
  record('Report response Content-Type is application/pdf', contentType?.includes('application/pdf'), contentType);
  const pdfBytes = await downloadRes.arrayBuffer();
  const pdfMagic = Buffer.from(pdfBytes.slice(0, 4)).toString('utf-8');
  record('Downloaded file has valid PDF magic bytes (%PDF)', pdfMagic === '%PDF', `magic: ${pdfMagic}, size: ${pdfBytes.byteLength} bytes`);

  console.log('\n--- 10. Dashboard Aggregate Metrics (Section 8.7 & PRD Ch. 20, 30.7) ---');
  const dashRes = await request('/api/dashboard/summary', {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('GET /api/dashboard/summary HTTP 200', dashRes.status === 200, `status: ${dashRes.status}`);
  const dashData = await dashRes.json();
  record('Dashboard metrics total_documents >= 2', dashData.total_documents >= 2, `total: ${dashData.total_documents}`);
  record('Dashboard metrics completed_count >= 2', dashData.completed_count >= 2, `completed: ${dashData.completed_count}`);

  console.log('\n--- 11. Error Contracts & Validation (PRD Ch. 30.8) ---');
  // 404
  const notFoundRes = await request('/api/documents/00000000-0000-0000-0000-000000000000/', {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('Resource not found returns 404', notFoundRes.status === 404, `status: ${notFoundRes.status}`);
  const notFoundData = await notFoundRes.json();
  record('Standard error code NOT_FOUND', notFoundData.error?.code === 'NOT_FOUND', notFoundData.error?.code);

  // 400 Same Document Comparison
  const selfCompRes = await request('/api/comparisons/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ document_a_id: doc1Id, document_b_id: doc1Id }),
  });
  record('Self-comparison rejected with 400', selfCompRes.status === 400, `status: ${selfCompRes.status}`);
  const selfCompData = await selfCompRes.json();
  record('Standard error code VALIDATION_ERROR', selfCompData.error?.code === 'VALIDATION_ERROR', selfCompData.error?.code);

  console.log('\n--- 12. Deletion Cascade (Section 8.2 & PRD Ch. 26.5) ---');
  const deleteRes = await request(`/api/documents/${doc1Id}/`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('DELETE /api/documents/{id}/ HTTP 204', deleteRes.status === 204, `status: ${deleteRes.status}`);

  const postDeleteRes = await request(`/api/documents/${doc1Id}/`, {
    headers: { 'Authorization': `Bearer ${accessToken}` },
  });
  record('Deleted document returns 404', postDeleteRes.status === 404);

  console.log('\n========================================');
  console.log(`🎉 ALL ${results.length} INTEGRATION CRITERIA PASSED!`);
  console.log('========================================\n');
}

run().catch(err => {
  console.error('\n❌ INTEGRATION VERIFICATION FAILED:\n', err);
  process.exit(1);
});
