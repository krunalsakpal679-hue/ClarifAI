import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';

export const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [readingLevel, setReadingLevel] = useState<'standard' | 'executive' | 'detailed'>('standard');

  const handleStartAnalysis = () => {
    // Generate a mock document ID and transition to the processing pipeline view
    const mockDocId = `doc_${Date.now().toString().slice(-6)}`;
    navigate(`/documents/${mockDocId}/processing`);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <Badge variant="info" size="sm" className="uppercase tracking-wider">
          Ingestion & Simplification
        </Badge>
        <h1 className="text-3xl font-serif font-bold text-primary-950">
          Upload Legal Document
        </h1>
        <p className="text-sm text-secondary-600">
          Upload a contract or agreement in PDF, DOCX, or TXT format for automated clause extraction and risk analysis.
        </p>
      </div>

      <Card elevation="sm">
        <CardHeader>
          <CardTitle className="text-base">Document Ingestion</CardTitle>
          <CardDescription>
            Maximum file size: 25MB. Text extraction and OCR processing are performed in isolated tenant pipelines.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Dropzone mock */}
          <div
            className="border-2 border-dashed border-secondary-300 hover:border-primary-500 rounded-xl p-8 text-center cursor-pointer transition-colors bg-secondary-50/50"
            onClick={() => setSelectedFile('Vendor_Master_Agreement_v2.pdf')}
          >
            <div className="w-12 h-12 rounded-full bg-primary-100 text-primary-800 flex items-center justify-center mx-auto mb-3 text-xl">
              📂
            </div>
            {selectedFile ? (
              <div className="space-y-1">
                <p className="text-sm font-semibold text-primary-900">{selectedFile}</p>
                <p className="text-xs text-secondary-500">2.4 MB &bull; Ready for processing</p>
                <span className="inline-block text-xs text-primary-600 underline pt-1">
                  Click to choose a different file
                </span>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm font-medium text-secondary-800">
                  Drag and drop your contract here, or <span className="text-primary-700 font-semibold underline">browse</span>
                </p>
                <p className="text-xs text-secondary-500">Supports PDF, DOCX, TXT</p>
              </div>
            )}
          </div>

          {/* Reading Level / Simplification Mode */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-secondary-700 uppercase tracking-wider">
              Simplification Reading Level
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(
                [
                  { id: 'executive', title: 'Executive', desc: 'High-level bullet summaries' },
                  { id: 'standard', title: 'Standard', desc: 'Balanced plain-English' },
                  { id: 'detailed', title: 'Detailed', desc: 'Thorough legal breakdown' },
                ] as const
              ).map((lvl) => (
                <button
                  key={lvl.id}
                  type="button"
                  onClick={() => setReadingLevel(lvl.id)}
                  className={`p-3 text-left rounded-lg border text-xs transition-colors ${
                    readingLevel === lvl.id
                      ? 'border-primary-600 bg-primary-50/60 ring-2 ring-primary-500/20'
                      : 'border-secondary-200 hover:border-secondary-300'
                  }`}
                >
                  <span className="block font-semibold text-secondary-900">{lvl.title}</span>
                  <span className="block text-[11px] text-secondary-500 mt-0.5">{lvl.desc}</span>
                </button>
              ))}
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex justify-between items-center pt-2">
          <Button
            variant="outline"
            size="md"
            onClick={() => navigate('/dashboard')}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleStartAnalysis}
          >
            Start Processing Pipeline &rarr;
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};
