"use client";

import { useState, useRef, useEffect } from "react";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8001";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [keyword, setKeyword] = useState("");
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [highlightData, setHighlightData] = useState<any>(null);
  const [wordsFound, setWordsFound] = useState<number | null>(null);
  const [imagePreview, setImagePreview] = useState("");
  const [pagesScanned, setPagesScanned] = useState<number | null>(null);
  const [totalPages, setTotalPages] = useState<number | null>(null);
  const [screenshots, setScreenshots] = useState<Record<string, string>>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [highlightPage, setHighlightPage] = useState(1);
  const [scanProgress, setScanProgress] = useState<string | null>(null);
  const [scanJobId, setScanJobId] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  useEffect(() => {
    return () => stopPolling();
  }, []);

  const uploadImage = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/ocr`, formData);
      setDocumentId(res.data.document_id);
      setWordsFound(res.data.words_found);
      setPagesScanned(null);
      setTotalPages(null);
      setScreenshots({});
      setCurrentPage(1);
      setScanProgress(null);
    } catch {
      alert("OCR Failed");
    }
    setLoading(false);
  };

  const scanWebsite = async () => {
    if (!url) return;
    setLoading(true);
    setScanProgress("Starting scan...");
    setPagesScanned(null);
    setTotalPages(null);
    setScreenshots({});
    setWordsFound(null);
    setDocumentId("");
    setResults(null);

    try {
      const res = await axios.post(`${API_BASE}/scan-website`, { url });
      const jobId: string = res.data.job_id;
      setScanJobId(jobId);
      setScanProgress(`Job created: ${jobId.slice(0, 8)}...`);

      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await axios.get(
            `${API_BASE}/scan-website/status/${jobId}`
          );
          const data = statusRes.data;

          if (data.progress) {
            setPagesScanned(data.progress.current_page);
            setTotalPages(data.progress.total_pages);
            setScanProgress(
              `Scanning page ${data.progress.current_page} of ${data.progress.total_pages}…`
            );
            if (data.progress.words_extracted > 0) {
              setScanProgress(
                `Scanning page ${data.progress.current_page} of ${data.progress.total_pages} – ${data.progress.words_extracted} words extracted`
              );
            }
          }

          if (data.status === "completed") {
            stopPolling();
            setLoading(false);
            const r = data.result;
            if (r) {
              setDocumentId(r.document_id);
              setWordsFound(r.total_words);
              setPagesScanned(r.pages_scanned);
              setTotalPages(r.total_pages);
              setScreenshots(r.screenshots || {});
              setCurrentPage(1);
              if (r.screenshot_url) setImagePreview(r.screenshot_url);
            }
            setScanProgress(
              r
                ? `Complete – ${r.pages_scanned} pages, ${r.total_words} words`
                : "Complete"
            );
          } else if (data.status === "failed") {
            stopPolling();
            setLoading(false);
            setScanProgress(`Failed: ${data.error || "Unknown error"}`);
            alert(`Scan failed: ${data.error || "Unknown error"}`);
          }
        } catch {
          stopPolling();
          setLoading(false);
          setScanProgress("Status check failed");
          alert("Website Scan Failed");
        }
      }, 1500);
    } catch (err: any) {
      setLoading(false);
      setScanProgress(null);
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Website Scan Failed";
      alert(msg);
    }
  };

  const searchKeyword = async () => {
    if (!documentId || !keyword) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/search`, {
        document_id: documentId,
        keyword,
      });
      setResults(res.data);
    } catch {
      alert("Search Failed");
    }
    setLoading(false);
  };

  const highlightKeyword = async () => {
    if (!documentId || !keyword) return;
    try {
      const res = await axios.post(`${API_BASE}/highlight`, {
        document_id: documentId,
        keyword,
        page_number: highlightPage,
      });
      setHighlightData(res.data);
    } catch {
      alert("Highlight Failed");
    }
  };

  const switchPage = (page: number) => {
    setCurrentPage(page);
    const url = screenshots[String(page)];
    if (url) setImagePreview(url);
  };

  const gotResult = documentId && wordsFound !== null;

  return (
    <main className="max-w-4xl mx-auto p-8 space-y-8">
      <h1 className="text-4xl font-bold">Universal Visual Search</h1>

      {gotResult && (
        <div className="border rounded-lg p-4">
          <h2 className="font-bold text-lg">Document Processed</h2>
          <p>Words Found: {wordsFound}</p>
          {pagesScanned !== null && totalPages !== null && (
            <p className="text-sm text-gray-600">
              Pages Scanned: {pagesScanned} / {totalPages}
            </p>
          )}
        </div>
      )}

      <div className="border p-4 rounded-lg space-y-4">
        <h2 className="font-bold">Upload Image</h2>
        <input
          type="file"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            setFile(f);
            setImagePreview(URL.createObjectURL(f));
          }}
        />
        <button
          onClick={uploadImage}
          className="bg-blue-600 text-white px-4 py-2 rounded"
        >
          Upload & OCR
        </button>
      </div>

      <div className="border p-4 rounded-lg space-y-4">
        <h2 className="font-bold">Scan Website</h2>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com"
          className="border p-2 w-full"
        />
        <button
          onClick={scanWebsite}
          disabled={loading}
          className="bg-green-600 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {loading ? "Scanning…" : "Scan Website"}
        </button>
        {scanProgress && (
          <p className="text-sm text-gray-600">{scanProgress}</p>
        )}
      </div>

      <div className="border p-4 rounded-lg space-y-4">
        <h2 className="font-bold">Search OCR Data</h2>
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Keyword"
          className="border p-2 w-full"
        />
        <div className="flex gap-2 items-center">
          <button
            onClick={searchKeyword}
            className="bg-purple-600 text-white px-4 py-2 rounded"
          >
            Search
          </button>
          {totalPages && totalPages > 1 && (
            <input
              type="number"
              min={1}
              max={totalPages}
              value={highlightPage}
              onChange={(e) =>
                setHighlightPage(
                  Math.max(1, Math.min(totalPages, parseInt(e.target.value) || 1))
                )
              }
              className="border p-2 w-20 text-center"
              title="Page number to highlight"
            />
          )}
          <button
            onClick={highlightKeyword}
            className="bg-orange-600 text-white px-4 py-2 rounded"
          >
            Highlight
          </button>
        </div>
      </div>

      {loading && !scanProgress && (
        <div className="text-lg font-semibold">Processing...</div>
      )}

      {results && (
        <div className="border rounded-lg p-4">
          <h2 className="font-bold text-lg mb-3">Search Results</h2>
          <p className="mb-4">Found {results.total_matches} matches</p>
          <div className="space-y-2">
            {results.matches.map((match: any, index: number) => (
              <div key={index} className="border rounded p-3">
                <p className="font-semibold">{match.text}</p>
                <p className="text-sm text-gray-600">
                  Confidence: {(match.confidence * 100).toFixed(1)}%
                </p>
                {match.page_number && (
                  <p className="text-sm text-blue-600">
                    Page: {match.page_number}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {totalPages && totalPages > 1 && (
        <div className="border rounded-lg p-4">
          <h2 className="font-bold text-lg mb-3">Page Navigation</h2>
          <div className="flex gap-2 flex-wrap">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => switchPage(p)}
                className={`px-3 py-1 rounded border ${
                  currentPage === p
                    ? "bg-blue-600 text-white"
                    : "bg-white text-blue-600"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {highlightData && (
        <div className="border rounded-lg p-4 mt-4">
          <h2 className="font-bold text-lg mb-4">Visual Comparison</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold mb-2">
                {totalPages && totalPages > 1
                  ? `Page ${highlightData.page_number || currentPage} – Original`
                  : "Original Image"}
              </h3>
              {imagePreview ? (
                <img src={imagePreview} alt="Original" className="border rounded" />
              ) : (
                <div className="border rounded p-8 text-center">
                  Original preview unavailable
                </div>
              )}
            </div>
            <div>
              <h3 className="font-semibold mb-2">
                {totalPages && totalPages > 1
                  ? `Page ${highlightData.page_number || currentPage} – Highlighted`
                  : "Highlighted Result"}
              </h3>
              {highlightData.highlighted_image_url ? (
                <img
                  src={highlightData.highlighted_image_url}
                  alt="Highlighted"
                  className="border rounded"
                />
              ) : (
                <div className="border rounded p-8 text-center">
                  No matches found on this page
                </div>
              )}
            </div>
          </div>
          <p className="mt-4">Matches Found: {highlightData.total_matches}</p>
        </div>
      )}
    </main>
  );
}
