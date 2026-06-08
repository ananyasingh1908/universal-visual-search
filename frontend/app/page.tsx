"use client";

import { useState } from "react";
import axios from "axios";

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

  const API = "http://127.0.0.1:8000";

  const uploadImage = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);

    try {
      const res = await axios.post(`${API}/ocr`, formData);

      setDocumentId(res.data.document_id);
      setWordsFound(res.data.words_found);
    } catch (err) {
      console.error(err);
      alert("OCR Failed");
    }

    setLoading(false);
  };

  const scanWebsite = async () => {
    if (!url) return;

    setLoading(true);

    try {
      const res = await axios.post(
  `${API}/scan-website`,
  { url }
);

console.log("SCAN RESPONSE:", res.data);

      setDocumentId(res.data.document_id);
      setWordsFound(res.data.words_found);

      if (res.data.screenshot_url) {
        setImagePreview(res.data.screenshot_url);
      }
      
    } catch (err) {
      console.error(err);
      alert("Website Scan Failed");
    }

    setLoading(false);
  };

  const searchKeyword = async () => {
  if (!documentId || !keyword) return;

  setLoading(true);

  try {
    const res = await axios.post(
      `${API}/search`,
      {
        document_id: documentId,
        keyword,
      }
    );

    console.log("SEARCH RESPONSE:", res.data);

    setResults(res.data);
  } catch (err) {
    console.error(err);
    alert("Search Failed");
  }

  setLoading(false);
};
  const highlightKeyword = async () => {
  if (!documentId || !keyword) return;

  try {
    const res = await axios.post(
      `${API}/highlight`,
      {
        document_id: documentId,
        keyword,
      }
    );

    console.log("HIGHLIGHT RESPONSE:", res.data);

    setHighlightData(res.data);
  } catch (err) {
    console.error(err);
    alert("Highlight Failed");
  }
};

  return (
    <main className="max-w-4xl mx-auto p-8 space-y-8">
      <h1 className="text-4xl font-bold">
        Universal Visual Search
      </h1>
      {wordsFound !== null && (
  <div className="border rounded-lg p-4">
    <h2 className="font-bold text-lg">
      Document Processed
    </h2>

    <p>
      Words Found: {wordsFound}
    </p>
  </div>
)}

      <div className="border p-4 rounded-lg space-y-4">
        <h2 className="font-bold">
          Upload Image
        </h2>

        <input
          type="file"
          onChange={(e) => {
            const selectedFile =
              e.target.files?.[0];

            if (!selectedFile) return;

            setFile(selectedFile);

            setImagePreview(
              URL.createObjectURL(selectedFile)
            );
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
        <h2 className="font-bold">
          Scan Website
        </h2>

        <input
          value={url}
          onChange={(e) =>
            setUrl(e.target.value)
          }
          placeholder="https://example.com"
          className="border p-2 w-full"
        />

        <button
          onClick={scanWebsite}
          className="bg-green-600 text-white px-4 py-2 rounded"
        >
          Scan Website
        </button>
      </div>

      <div className="border p-4 rounded-lg space-y-4">
        <h2 className="font-bold">
          Search OCR Data
        </h2>

      

        <input
          value={keyword}
          onChange={(e) =>
            setKeyword(e.target.value)
          }
          placeholder="Keyword"
          className="border p-2 w-full"
        />

        <div className="flex gap-2">
  <button
    onClick={searchKeyword}
    className="bg-purple-600 text-white px-4 py-2 rounded"
  >
    Search
  </button>

  <button
    onClick={highlightKeyword}
    className="bg-orange-600 text-white px-4 py-2 rounded"
  >
    Highlight
  </button>
</div>
      </div>

      {loading && (
        <div className="text-lg font-semibold">
          Processing...
        </div>
      )}

            {results && (
              <div className="border rounded-lg p-4">
                <h2 className="font-bold text-lg mb-3">
                  Search Results
                </h2>

                <p className="mb-4">
                  Found {results.total_matches} matches
                </p>

                <div className="space-y-2">
                  {results.matches.map(
                    (match: any, index: number) => (
                      <div
                        key={index}
                        className="border rounded p-3"
                      >
                        <p className="font-semibold">
                          {match.text}
                        </p>

                        <p className="text-sm text-gray-600">
                          Confidence:
                          {" "}
                          {(match.confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          
      {highlightData && (
  <div className="border rounded-lg p-4 mt-4">
    <h2 className="font-bold text-lg mb-4">
      Visual Comparison
    </h2>

    <div className="grid md:grid-cols-2 gap-4">
      <div>
        <h3 className="font-semibold mb-2">
          Original Image
        </h3>

        {imagePreview ? (
  <img
    src={imagePreview}
    alt="Original"
    className="border rounded"
  />
) : (
  <div className="border rounded p-8 text-center">
    Original preview unavailable
  </div>
)}
      </div>

      <div>
        <h3 className="font-semibold mb-2">
          Highlighted Result
        </h3>

        <img
          src={highlightData.highlighted_image_url}
          alt="Highlighted"
          className="border rounded"
        />
      </div>
    </div>

    <p className="mt-4">
      Matches Found:
      {" "}
      {highlightData.total_matches}
    </p>
  </div>
)}
    </main>
  );
}