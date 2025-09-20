import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { motion, AnimatePresence } from "framer-motion";

export default function App() {
  // Detect local vs production
  const API_BASE = import.meta.env.MODE === "development"
      ? "http://localhost:7860" // local Flask server
      : import.meta.env.VITE_API_URL; // production (Railway)

  const [songText, setSongText] = useState("");
  const [jobs, setJobs] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const pollRef = useRef(null);
  const [order, setOrder] = useState("latest");

  const tutorialSteps = [
    "🎵 Paste song lines or upload a .txt containing one song per line (e.g. Shape of You - Ed Sheeran).",
    "🚀 Click Start Download — backend searches Spotify, finds a YouTube match, downloads audio, and tags MP3s.",
    "📝 When the job completes, files appear in the Downloaded files section and you can download them.",
  ];

  useEffect(() => {
    fetchFiles();
    return () => clearInterval(pollRef.current);
  }, []);

  async function fetchFiles(selectedOrder) {
    try {
      const orderToUse = selectedOrder || order;
      const res = await axios.get(`${API_BASE}/api/files?order=${orderToUse}`);
      setFiles(res.data.files || []);
      setOrder(orderToUse);
    } catch (e) {
      console.error("fetchFiles error", e);
    }
  }

  async function startDownload() {
    const list = songText
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
    if (!list.length) return alert("Add at least one song line");
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/api/download`, { songs: list });
      const id = res.data.job_id;
      setJobId(id);
      setJobs(res.data.initial || []);
      pollRef.current = setInterval(() => pollStatus(id), 1500);
    } catch (e) {
      console.error("startDownload error", e);
      alert("Failed to start job");
      setLoading(false);
    }
  }

  async function pollStatus(id) {
    try {
      const res = await axios.get(`${API_BASE}/api/status/${id}`);
      setJobs(res.data.jobs || []);
      if (res.data.state === "done" || res.data.state === "failed") {
        clearInterval(pollRef.current);
        setLoading(false);
        fetchFiles();
      }
    } catch (e) {
      console.error("pollStatus error", e);
    }
  }

  function downloadFile(name) {
    window.open(
      `${API_BASE}/api/file/${encodeURIComponent(name)}`,
      "_blank",
      "noopener"
    );
  }

  function AccordionStep({ step, index }) {
    const [open, setOpen] = useState(false);
    return (
      <div className="bg-slate-800/40 rounded-lg">
        <button
          onClick={() => setOpen(!open)}
          className="w-full p-3 flex justify-between items-center font-semibold text-accent"
        >
          <span>{`Step ${index + 1}`}</span>
          <span>{open ? "−" : "+"}</span>
        </button>
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: open ? 1 : 0, height: open ? "auto" : 0 }}
          transition={{ duration: 0.3 }}
          className="p-3 text-slate-300"
        >
          {step}
        </motion.div>
      </div>
    );
  }

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-4 sm:p-6
                    bg-gradient-to-br from-slate-800 via-slate-900 to-black"
    >
      <div
        className="w-full max-w-6xl bg-gradient-to-br from-slate-800/60 to-slate-900/40
                      border border-slate-700/40 rounded-2xl p-4 sm:p-8 backdrop-blur-lg shadow-2xl"
      >
        <div className="flex items-center justify-between mb-6">
          <motion.h1
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="text-2xl sm:text-4xl font-extrabold tracking-tight
                       text-xxl font-extrabold bg-gradient-to-r from-blue-600 via-teal-500 to-cyan-600 bg-clip-text text-transparent tracking-wide"
          >
            {/* <h1 className="text-xxl font-extrabold bg-gradient-to-r from-blue-600 via-teal-500 to-cyan-600 bg-clip-text text-transparent tracking-wide"> */}
              TuneFlow
            {/* </h1> */}
          </motion.h1>

          <div className="flex gap-2 sm:gap-3">
            <button
              onClick={() => fetchFiles()}
              className="px-3 sm:px-4 py-2 rounded-lg bg-slate-700/40 hover:bg-slate-700/60"
            >
              Refresh
            </button>
            <a
              href="#tutorial"
              className="px-3 sm:px-4 py-2 rounded-lg bg-accent/90 hover:bg-accent"
            >
              Tutorial
            </a>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-y-6 gap-x-6">
          <motion.div
            initial={{ scale: 0.98 }}
            animate={{ scale: 1 }}
            className="col-span-1 lg:col-span-2 bg-slate-800/40 rounded-xl p-4 sm:p-6"
          >
            <label className="block text-sm mb-2">
              Paste song names (one per line) or upload .txt
            </label>

            <textarea
              value={songText}
              onChange={(e) => setSongText(e.target.value)}
              rows={10}
              className="w-full p-3 sm:p-4 rounded-lg bg-neutral-900 text-slate-100 placeholder-slate-400"
              placeholder="Example: Shape of You - Ed Sheeran"
            />

            <div className="flex flex-col sm:flex-row sm:justify-between items-center gap-3 mt-4 w-full">
              <button
                onClick={startDownload}
                disabled={loading}
                className="w-full sm:w-[180px] px-6 py-3 rounded-full bg-accent text-white font-semibold shadow-lg hover:scale-105 disabled:opacity-60 text-center"
              >
                {loading ? (
                  <motion.div
                    className="flex items-center justify-center gap-2"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    <motion.svg
                      className="h-5 w-5 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      animate={{ rotate: 360 }}
                      transition={{
                        repeat: Infinity,
                        duration: 1,
                        ease: "linear",
                      }}
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                      />
                    </motion.svg>
                    <span>Downloading...</span>
                  </motion.div>
                ) : (
                  "Start Download"
                )}
              </button>

              <input
                type="file"
                accept=".txt"
                onChange={async (e) => {
                  const f = e.target.files?.[0];
                  if (!f) return;
                  try {
                    const t = await f.text();
                    setSongText((prev) => (prev ? prev + "\n" : "") + t);
                  } catch (err) {
                    console.error("file read error", err);
                  }
                }}
                className="w-full sm:flex-1 text-sm px-3 py-2 rounded-md border bg-slate-900/40 hover:bg-slate-900/60 cursor-pointer"
              />

              <button
                onClick={() => setSongText("")}
                className="w-full sm:w-[120px] px-4 py-3 rounded-md border bg-slate-800/40 hover:bg-slate-800/60"
              >
                Clear
              </button>
            </div>

            <div className="mt-6">
              <h3 className="font-semibold mb-2">Job progress</h3>
              <div className="grid gap-2">
                <AnimatePresence>
                  {jobs.map((j) => (
                    <motion.div
                      layout
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 6 }}
                      key={j.name}
                      className="flex items-center justify-between p-3 bg-slate-900/40 rounded-md"
                    >
                      <div>
                        <div className="font-medium">{j.name}</div>
                        <div className="text-sm text-slate-400">
                          {j.status} {j.message ? `— ${j.message}` : ""}
                        </div>
                      </div>

                      <div className="w-32 sm:w-48">
                        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            style={{ width: `${j.progress || 0}%` }}
                            className="h-full bg-accent transition-all"
                          />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="col-span-1 bg-slate-800/30 rounded-xl p-4 sm:p-6"
          >
            <h3 className="font-semibold mb-3">Downloaded files</h3>

            <div className="flex justify-end mb-3">
              <div className="flex bg-slate-900/40 rounded-full p-1">
                <button
                  onClick={() => fetchFiles("latest")}
                  className={`px-3 py-1 rounded-full text-sm ${
                    order === "latest"
                      ? "bg-accent text-white"
                      : "text-slate-300 hover:text-white"
                  }`}
                >
                  Latest
                </button>
                <button
                  onClick={() => fetchFiles("oldest")}
                  className={`px-3 py-1 rounded-full text-sm ${
                    order === "oldest"
                      ? "bg-accent text-white"
                      : "text-slate-300 hover:text-white"
                  }`}
                >
                  Oldest
                </button>
              </div>
            </div>

            <div
              className="flex flex-col gap-2 max-h-64 overflow-y-auto pr-1
                            scrollbar-thin scrollbar-thumb-cyan-500/70 scrollbar-track-slate-800/30 hover:scrollbar-thumb-cyan-500/90 transition-colors"
            >
              {files.length === 0 && (
                <div className="text-sm text-slate-400">
                  No files yet — start a job to generate MP3s.
                </div>
              )}
              {files.map((f) => (
                <div
                  key={f}
                  className="flex items-center justify-between bg-slate-900/30 p-2 sm:p-3 rounded-md"
                >
                  <div className="truncate max-w-[160px] sm:max-w-[250px]">
                    {f}
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => downloadFile(f)}
                      className="px-2 sm:px-3 py-1 rounded-md border"
                    >
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <hr className="my-4 border-slate-700/30" />
            <div className="text-xs text-slate-400">
              Built with ❤️ by{" "}
              <span className="text-accent font-semibold">
                Aryan Palaspagar
              </span>{" "}
              — a passionate CSE Data Science engineer exploring Web
              Development, AI/ML, and Cloud.
            </div>
          </motion.div>
        </div>

        <div id="tutorial" className="mt-8">
          <h4 className="font-semibold mb-4 text-accent">Quick Tutorial</h4>

          <div className="hidden md:grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tutorialSteps.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="bg-slate-800/40 p-4 rounded-xl shadow-lg hover:scale-105 transition-transform"
              >
                <span className="font-bold text-accent">{`Step ${i + 1}`}</span>
                <p className="mt-2 text-slate-300">{step}</p>
              </motion.div>
            ))}
          </div>

          <div className="md:hidden flex flex-col gap-2">
            {tutorialSteps.map((step, i) => (
              <AccordionStep key={i} index={i} step={step} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
