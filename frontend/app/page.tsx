"use client";

import { useState, useRef, useEffect } from "react";
import axios from "axios";
import { cn } from "@/lib/utils";

const API_BASE = "http://127.0.0.1:8000";

type Newspaper = {
  name: string;
  language: "English" | "Hindi" | "Marathi";
  columnKey?: NewspaperColumn;
};

type NewspaperColumn =
  | "Lokmat"
  | "Sakal"
  | "Loksatta"
  | "MTimes"
  | "PNagari"
  | "Deshonnati"
  | "Navbharat"
  | "DBhaskar"
  | "Hitavada";

type DistrictAvailability = {
  district: string;
  availability: Record<NewspaperColumn, boolean>;
};

const VERIFIED_NEWSPAPERS: Record<Newspaper["language"], Newspaper[]> = {
  English: [
    { name: "The Hitavada", language: "English", columnKey: "Hitavada" },
    { name: "The Hitavada City Line", language: "English", columnKey: "Hitavada" },
    { name: "The Hitavada Vidarbha Line", language: "English", columnKey: "Hitavada" },
    { name: "Times of India Nagpur", language: "English" },
  ],
  Hindi: [
    { name: "Lokmat Samachar", language: "Hindi" },
    { name: "Lokmat Samachar Apna Nagpur", language: "Hindi" },
    { name: "Lokmat Samachar Apna Vidarbha", language: "Hindi" },
    { name: "Navbharat", language: "Hindi", columnKey: "Navbharat" },
    { name: "Navbharat Nagpur Plus", language: "Hindi", columnKey: "Navbharat" },
  ],
  Marathi: [
    { name: "Lokmat Nagpur", language: "Marathi", columnKey: "Lokmat" },
    { name: "Lokmat Hello Nagpur", language: "Marathi", columnKey: "Lokmat" },
    { name: "Lokmat Hello Wardha", language: "Marathi", columnKey: "Lokmat" },
    { name: "Maharashtra Times Nagpur", language: "Marathi", columnKey: "MTimes" },
    { name: "Maharashtra Times Nagpur Plus", language: "Marathi", columnKey: "MTimes" },
    { name: "Navarashtra", language: "Marathi" },
    { name: "Lokvahini", language: "Marathi" },
    { name: "Lokshahi Varta Edition 11", language: "Marathi" },
    { name: "Lokshahi Varta Edition 16", language: "Marathi" },
    { name: "Deshonnati", language: "Marathi", columnKey: "Deshonnati" },
    { name: "Loksatta Nagpur", language: "Marathi", columnKey: "Loksatta" },
  ],
};

const DISTRICT_AVAILABILITY: DistrictAvailability[] = [
  {
    district: "Mumbai City",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Mumbai Suburban",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Thane",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Palghar",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Raigad",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Ratnagiri",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Sindhudurg",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Pune",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Satara",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Sangli",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Kolhapur",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Solapur",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Nashik",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Ahmednagar",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Dhule",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Nandurbar",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Jalgaon",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Chh. Sambhajinagar",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: false,
      DBhaskar: true,
      Hitavada: false,
    },
  },
  {
    district: "Jalna",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Beed",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Dharashiv",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Latur",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Nanded",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Parbhani",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Hingoli",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: false,
      Navbharat: false,
      DBhaskar: false,
      Hitavada: false,
    },
  },
  {
    district: "Nagpur",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: true,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Wardha",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: false,
      MTimes: false,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Bhandara",
    availability: {
      Lokmat: true,
      Sakal: false,
      Loksatta: false,
      MTimes: false,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Gondia",
    availability: {
      Lokmat: true,
      Sakal: false,
      Loksatta: false,
      MTimes: false,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Chandrapur",
    availability: {
      Lokmat: true,
      Sakal: false,
      Loksatta: false,
      MTimes: false,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Gadchiroli",
    availability: {
      Lokmat: true,
      Sakal: false,
      Loksatta: false,
      MTimes: false,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Amravati",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Akola",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
  {
    district: "Washim",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: false,
      MTimes: false,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: false,
      Hitavada: true,
    },
  },
  {
    district: "Buldhana",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: true,
      MTimes: true,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: false,
      Hitavada: true,
    },
  },
  {
    district: "Yavatmal",
    availability: {
      Lokmat: true,
      Sakal: true,
      Loksatta: false,
      MTimes: false,
      PNagari: false,
      Deshonnati: true,
      Navbharat: true,
      DBhaskar: true,
      Hitavada: true,
    },
  },
];

type OCRMatch = {
  text: string;
  confidence: number;
  page_number?: number;
  is_headline?: boolean;
};

type OCRSearchResponse = {
  document_id: string;
  keyword: string;
  keywords?: string[];
  total_matches: number;
  matches: Array<OCRMatch & { matched_keyword?: string | null }>;
};

type OCRUploadResponse = {
  document_id: string;
  words_found: number;
  headline_text?: string;
  headline_lines?: string[];
};

type HighlightResponse = {
  highlighted_image_url: string | null;
  total_matches: number;
  page_number?: number;
  viewer_url?: string;
};

type ScanResult = {
  document_id: string;
  pages_scanned: number;
  total_pages: number;
  total_words: number;
  screenshots?: Record<string, string>;
  screenshot_url?: string;
  page_headlines?: Record<string, string>;
  headline_text?: string;
};

type ScanStatusResponse = {
  job_id: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress?: {
    current_page: number;
    total_pages: number;
    words_extracted: number;
  };
  result?: ScanResult;
  error?: string;
};

const getErrorMessage = (err: unknown, fallback: string) => {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
  }

  if (err instanceof Error) {
    return err.message;
  }

  return fallback;
};

const Page = () => {
  const [file, setFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [results, setResults] = useState<OCRSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [highlightData, setHighlightData] = useState<HighlightResponse | null>(null);
  const [wordsFound, setWordsFound] = useState<number | null>(null);
  const [headlineText, setHeadlineText] = useState("");
  const [pageHeadlines, setPageHeadlines] = useState<Record<string, string>>({});
  const [imagePreview, setImagePreview] = useState("");
  const [pagesScanned, setPagesScanned] = useState<number | null>(null);
  const [totalPages, setTotalPages] = useState<number | null>(null);
  const [screenshots, setScreenshots] = useState<Record<string, string>>({});
  const [currentPage, setCurrentPage] = useState(1);
  const [highlightPage, setHighlightPage] = useState(1);
  const [scanProgress, setScanProgress] = useState<string | null>(null);
  const [selectedNewspaper, setSelectedNewspaper] = useState<Newspaper | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<string>("");
  const [selectedDate, setSelectedDate] = useState<string>("");
  const [showCalendar, setShowCalendar] = useState(false);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [showDropdown, setShowDropdown] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };

  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year: number, month: number) => {
    return new Date(year, month, 1).getDay();
  };

  const navigateCalendarMonth = (direction: number) => {
    setCurrentDate(prev => new Date(prev.getFullYear(), prev.getMonth() + direction, 1));
  };

  const selectDate = (date: string) => {
    setSelectedDate(date);
    setShowCalendar(false);
  };

  const handleNewspaperChange = (newspaperName: string) => {
    const newspaper = Object.values(VERIFIED_NEWSPAPERS).flat().find(n => n.name === newspaperName);
    if (newspaper) {
      setSelectedNewspaper(newspaper);
      setSelectedRegion("");
      setShowDropdown(false);
      setSearchTerm("");
    }
  };

  const openCalendar = () => {
    setShowCalendar(true);
  };

  const filteredNewspapers = Object.entries(VERIFIED_NEWSPAPERS).reduce((acc, [language, newspapers]) => {
    const filtered = newspapers.filter(newspaper =>
      newspaper.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    if (filtered.length > 0) {
      acc[language as keyof typeof VERIFIED_NEWSPAPERS] = filtered;
    }
    return acc;
  }, {} as typeof VERIFIED_NEWSPAPERS);

  const selectedNewspaperName = selectedNewspaper?.name || "";

  const daysInMonth = getDaysInMonth(currentDate.getFullYear(), currentDate.getMonth());
  const firstDayOfMonth = getFirstDayOfMonth(currentDate.getFullYear(), currentDate.getMonth());

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest(".dropdown-container")) {
        setShowDropdown(false);
      }
      if (!target.closest(".calendar-container") && showCalendar) {
        setShowCalendar(false);
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [showCalendar]);

  useEffect(() => {
    return () => stopPolling();
  }, []);

  const uploadImage = async () => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    try {
      const res = await axios.post<OCRUploadResponse>(`${API_BASE}/ocr`, formData);
      setDocumentId(res.data.document_id);
      setWordsFound(res.data.words_found);
      setHeadlineText(res.data.headline_text || "");
      setResults(null);
      setHighlightData(null);
      setPageHeadlines({});
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
    if (!selectedNewspaper) {
      alert("Please select a newspaper");
      return;
    }
    if (!selectedDate) {
      alert("Please select a date");
      return;
    }
    if (!selectedNewspaper.name) {
      alert("Please select a valid newspaper");
      return;
    }

    setLoading(true);
    setScanProgress("Starting scan...");
    setPagesScanned(null);
    setTotalPages(null);
    setScreenshots({});
    setWordsFound(null);
    setHeadlineText("");
    setHighlightData(null);
    setPageHeadlines({});
    setDocumentId("");
    setResults(null);

    try {
      const res = await axios.post<{ job_id: string }>(`${API_BASE}/resolve-and-scan`, {
        newspaper: selectedNewspaper.name,
        date: selectedDate,
        page: 1
      });
      const jobId: string = res.data.job_id;
      setScanProgress(`Job created: ${jobId.slice(0, 8)}...`);

      stopPolling();
      pollRef.current = setInterval(async () => {
        try {
          const statusRes = await axios.get<ScanStatusResponse>(
            `${API_BASE}/scan-website/status/${jobId}`
          );
          const data = statusRes.data;

          if (data.progress) {
            setPagesScanned(data.progress.current_page);
            setTotalPages(data.progress.total_pages);
            setScanProgress(
              `Scanning page ${data.progress.current_page} of ${data.progress.total_pages}...`
            );
            if (data.progress.words_extracted > 0) {
              setScanProgress(
                `Scanning page ${data.progress.current_page} of ${data.progress.total_pages} - ${data.progress.words_extracted} words extracted`
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
              setHeadlineText(r.headline_text || "");
              setPageHeadlines(r.page_headlines || {});
              setPagesScanned(r.pages_scanned);
              setTotalPages(r.total_pages);
              setScreenshots(r.screenshots || {});
              setCurrentPage(1);
              if (r.screenshot_url) setImagePreview(r.screenshot_url);
            }
            setScanProgress(
              r
                ? `Complete - ${r.pages_scanned} pages, ${r.total_words} words`
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
    } catch (err: unknown) {
      setLoading(false);
      setScanProgress(null);
      const msg = getErrorMessage(err, "Website Scan Failed");
      alert(msg);
    }
  };

  const searchNews = async () => {
    if (!documentId) return;
    setLoading(true);
    setHighlightData(null);
    try {
      const res = await axios.post<OCRSearchResponse>(`${API_BASE}/search`, {
        document_id: documentId,
      });
      setResults(res.data);

      const firstPreviewPage =
        res.data.matches.find((match) => match.page_number)?.page_number ??
        res.data.matches[0]?.page_number ??
        1;

      if (res.data.total_matches > 0) {
        setHighlightPage(firstPreviewPage);
        try {
          const previewRes = await axios.post<HighlightResponse>(`${API_BASE}/highlight`, {
            document_id: documentId,
            page_number: firstPreviewPage,
          });
          setHighlightData(previewRes.data);
        } catch {
          setHighlightData(null);
        }
      }
    } catch {
      alert("Search Failed");
    }
    setLoading(false);
  };

  const highlightNews = async () => {
    if (!documentId) return;
    try {
      const res = await axios.post<HighlightResponse>(`${API_BASE}/highlight`, {
        document_id: documentId,
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
    setHeadlineText(pageHeadlines[String(page)] || "");
  };

  const selectedColumnKey = selectedNewspaper?.columnKey;

  const getRegionAvailable = (district: string) => {
    if (!selectedColumnKey) return false;

    const entry = DISTRICT_AVAILABILITY.find((item) => item.district === district);
    return entry?.availability[selectedColumnKey] ?? false;
  };

  const gotResult = documentId && wordsFound !== null;

  return (
    <main className="max-w-4xl mx-auto p-8 space-y-8">
      <h1 className="text-4xl font-bold">Universal Visual Search</h1>

      {gotResult && (
        <div className="border rounded-lg p-4">
          <h2 className="font-bold text-lg">Document Processed</h2>
          <p>Words Found: {wordsFound}</p>
          {headlineText && (
            <p className="text-sm text-gray-700 mt-1">
              <span className="font-semibold">Headline:</span> {headlineText}
            </p>
          )}
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
        <h2 className="font-bold">Select Date</h2>
        <div className="relative calendar-container z-50">
          <input
            type="text"
            value={selectedDate ? new Date(selectedDate + "T00:00:00").toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : ""}
            placeholder="Select Date"
            className="border p-2 w-full cursor-pointer dark:text-white dark:bg-gray-800 dark:border-gray-600 relative z-50"
            onClick={openCalendar}
            readOnly
            required
          />
          <button
            type="button"
            onClick={openCalendar}
            className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded z-50"
          >
            📅
          </button>
          {showCalendar && (
            <div className="absolute top-full mt-2 p-4 bg-white dark:bg-gray-800 border rounded-lg shadow-lg z-50 w-72">
              <div className="flex justify-between items-center mb-4">
                <button
                  onClick={() => navigateCalendarMonth(-1)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  ←
                </button>
                <h3 className="font-semibold">
                  {currentDate.getFullYear()}/{currentDate.getMonth() + 1}
                </h3>
                <button
                  onClick={() => navigateCalendarMonth(1)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  →
                </button>
              </div>
              <div className="grid grid-cols-7 gap-1">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="text-center text-xs font-semibold text-gray-600 dark:text-gray-400">
                    {day}
                  </div>
                ))}
                {Array.from({ length: firstDayOfMonth }, (_, i) => (
                  <div key={`empty-${i}`} className="text-center p-1"></div>
                ))}
                {Array.from({ length: daysInMonth }, (_, i) => {
                  const formatLocalDate = (date: Date) =>
                  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
                  const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), i + 1);
                  const isSelected = selectedDate === formatLocalDate(date);                  
                  const isWeekend = date.getDay() === 0 || date.getDay() === 6;
                return (
                    <button
                      key={i + 1}
                      onClick={() => selectDate(formatLocalDate(date))}
                      className={cn(
                        "p-2 text-sm rounded hover:bg-blue-50 dark:hover:bg-blue-900/20",
                        isSelected ? "bg-blue-600 text-white" : "",
                        isWeekend ? "text-red-600 dark:text-red-400" : ""
                      )}
                    >
                      {i + 1}
                    </button>
                  );
                })}
              </div>
              <div className="flex justify-end mt-4">
                <button
                  onClick={() => setShowCalendar(false)}
                  className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  OK
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="border p-4 rounded-lg space-y-4">
        <h2 className="font-bold">Search OCR Data</h2>
        <p className="text-sm text-gray-600">
          This search uses a locked backend keyword set for English, Hindi, and Marathi
          electricity and newspaper terms. The keyword list cannot be edited from the UI.
          Search will also auto-open a preview for the first matching page when results are found.
        </p>
        <div className="flex gap-2 items-center flex-wrap">
          <button
            onClick={searchNews}
            className="bg-purple-600 text-white px-4 py-2 rounded"
          >
            Search News Keywords
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
            onClick={highlightNews}
            className="bg-orange-600 text-white px-4 py-2 rounded"
          >
            Highlight Matches
          </button>
        </div>
      </div>

      <div className="border rounded-lg p-4 space-y-5">
        <div>
          <h2 className="font-bold text-lg">Newspaper Menu</h2>
          <p className="text-sm text-gray-600 text-pretty">
            Choose a newspaper below. The buttons are clickable and will hold the
            selection until you tell me what action to attach next.
          </p>
        </div>

        <div className="dropdown-container relative">
          <h2 className="font-bold mb-2">Select Newspaper</h2>
          <div className="relative">
            <div
              onClick={() => setShowDropdown(!showDropdown)}
              className="border p-2 w-full rounded-md cursor-pointer bg-white dark:bg-gray-800 dark:text-white dark:border-gray-600 flex justify-between items-center"
            >
              <span className={selectedNewspaperName ? "text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400"}>
                {selectedNewspaperName || "Select Newspaper"}
              </span>
              <span className="text-gray-500 dark:text-gray-400">▼</span>
            </div>
            {showDropdown && (
              <div className="absolute top-full mt-1 w-full bg-white dark:bg-gray-800 border rounded-md shadow-lg z-50 max-h-60 overflow-y-auto">
                <div className="p-2 border-b dark:border-gray-700">
                  <input
                    type="text"
                    placeholder="Search newspapers..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full p-2 text-sm border rounded dark:bg-gray-700 dark:text-white dark:border-gray-600"
                    onClick={(e) => e.stopPropagation()}
                  />
                </div>
                {Object.entries(filteredNewspapers).map(([language, newspapers]) => (
                  <div key={language}>
                    <div className="px-3 py-2 text-xs font-semibold text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900">
                      {language} Newspapers
                    </div>
                    {newspapers.map((newspaper) => {
                      const isSelected =
                        selectedNewspaper?.name === newspaper.name &&
                        selectedNewspaper.language === newspaper.language;

                      return (
                        <div
                          key={`${newspaper.language}-${newspaper.name}`}
                          onClick={() => handleNewspaperChange(newspaper.name)}
                          className={cn(
                            "px-3 py-2 cursor-pointer text-sm hover:bg-gray-50 dark:hover:bg-gray-700",
                            isSelected ? "bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400" : "text-gray-800 dark:text-gray-200"
                          )}
                        >
                          {newspaper.name}
                        </div>
                      );
                    })}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-md border bg-gray-50 p-3 text-sm text-gray-700 space-y-3">
          {selectedNewspaper ? (
            <>
              <div>
                Selected newspaper:{" "}
                <span className="font-semibold">{selectedNewspaper.name}</span> (
                {selectedNewspaper.language})
              </div>
              {!selectedColumnKey && (
                <div className="text-xs text-gray-500">
                  This newspaper is not included in the district availability table yet, so
                  every region is marked - for now.
                </div>
              )}

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3">
                  <h4 className="font-semibold text-gray-900">Select Region</h4>
                  <span className="text-xs text-gray-500">
                    ✓ = available, - = not available
                  </span>
                </div>

                <label className="block">
                  <span className="sr-only">Select region</span>
                  <select
                    value={selectedRegion}
                    onChange={(e) => setSelectedRegion(e.target.value)}
                    className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900"
                  >
                    <option value="">Choose a district</option>
                    {DISTRICT_AVAILABILITY.map(({ district }) => {
                      const available = getRegionAvailable(district);
                      return (
                        <option key={district} value={district}>
                          {district} {available ? "✓" : "-"}
                        </option>
                      );
                    })}
                  </select>
                </label>

                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {DISTRICT_AVAILABILITY.map(({ district }) => {
                    const available = getRegionAvailable(district);
                    const isSelected = selectedRegion === district;

                    return (
                      <button
                        key={district}
                        type="button"
                        onClick={() => setSelectedRegion(district)}
                        aria-pressed={isSelected}
                        className={cn(
                          "flex items-center justify-between rounded-md border px-3 py-2 text-left text-sm",
                          "hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2",
                          isSelected
                            ? "border-gray-900 bg-gray-900 text-white"
                            : "border-gray-300 bg-white text-gray-800"
                        )}
                      >
                        <span className="font-medium text-pretty">{district}</span>
                        <span
                          className={cn(
                            "ml-3 text-base font-semibold",
                            isSelected ? "text-white" : "text-gray-700"
                          )}
                        >
                          {available ? "✓" : "-"}
                        </span>
                      </button>
                    );
                  })}
                </div>

                <div className="rounded-md border border-gray-200 bg-white p-3 text-sm text-gray-700">
                  {selectedRegion ? (
                    <>
                      <span className="font-semibold">{selectedRegion}</span>{" "}
                      {getRegionAvailable(selectedRegion)
                        ? "is available for this newspaper."
                        : "is not available for this newspaper."}
                    </>
                  ) : (
                    "Choose a district to see availability for the selected newspaper."
                  )}
                </div>
              </div>
            </>
          ) : (
            "No newspaper selected yet."
          )}
        </div>
      </div>

      {loading && !scanProgress && (
        <div className="text-lg font-semibold">Processing...</div>
      )}

      {results && (
        <div className="border rounded-lg p-4">
          <h2 className="font-bold text-lg mb-3">Search Results</h2>
          {results.keywords && (
            <p className="mb-2 text-sm text-gray-600">
              Locked keyword set active: {results.keywords.length} terms across English,
              Hindi, and Marathi.
            </p>
          )}
          <p className="mb-4">Found {results.total_matches} matches</p>
          <div className="space-y-2">
            {results.matches.map((match, index: number) => (
              <div key={index} className="border rounded p-3">
                <p className="font-semibold">{match.text}</p>
                <p className="text-sm text-gray-600">
                  Confidence: {(match.confidence * 100).toFixed(1)}%
                </p>
                {match.matched_keyword && (
                  <p className="text-sm text-emerald-700">
                    Matched keyword: {match.matched_keyword}
                  </p>
                )}
                {match.page_number && (
                  <p className="text-sm text-blue-600">
                    Page: {match.page_number}
                  </p>
                )}
                {match.is_headline && (
                  <p className="text-sm font-semibold text-amber-600">
                    Headline
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
          {highlightData.viewer_url && (
            <div className="mt-4">
              <a 
                href={highlightData.viewer_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-block px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                Open Interactive Viewer
              </a>
            </div>
          )}
        </div>
      )}
    </main>
  );
}

export default Page
