import { useEffect, useState } from "react";
import { Card } from "../components/common/Card";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorMessage } from "../components/common/ErrorMessage";
import SentimentTrendChart from "../components/charts/SentimentTrendChart";
import clsx from "clsx";

/* ---------------- CONSTANTS ---------------- */

const TICKERS = ["NVDA", "AMZN", "AXON", "AAPL", "ORCL", "MSFT", "JPM", "META", "TSLA", "AMD"];
const RANGES  = ["1D", "1W", "1M"] as const;
const API_BASE = "http://localhost:8001/api/v1";

type Range = typeof RANGES[number];

/* ---------------- TYPES ---------------- */

interface NewsItem {
  title:       string;
  description: string;
  url:         string;
  source:      string;
  publishedAt: string;
  sentiment:   "positive" | "negative" | "neutral";
  score:       number;
}

interface SentimentData {
  date:           string;
  sentimentScore: number;
}

/* ---------------- COMPONENT ---------------- */

export default function Analytics() {
  const [ticker,    setTicker]    = useState("AAPL");
  const [range,     setRange]     = useState<Range>("1W");
  const [news,      setNews]      = useState<NewsItem[]>([]);
  const [trendData, setTrendData] = useState<SentimentData[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError(null);

        const res = await fetch(`${API_BASE}/news?ticker=${ticker}&range=${range}`);
        if (!res.ok) throw new Error(`Server error: ${res.status}`);

        const data = await res.json();
        setNews(data.news ?? []);
        setTrendData(data.trend ?? []);
      } catch (e: any) {
        setError(e.message || "Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [ticker, range]);

  /* ---------------- HELPERS ---------------- */

  const sentimentColor = (sentiment: string) =>
    clsx(
      "px-2 py-1 text-xs rounded-full font-semibold",
      sentiment === "positive" && "bg-green-100 text-green-700",
      sentiment === "negative" && "bg-red-100 text-red-700",
      sentiment === "neutral"  && "bg-gray-100 text-gray-700"
    );

  /* ---------------- UI ---------------- */

  return (
    <div className="space-y-6">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          Analytics Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Live news insights and sentiment trends
        </p>
      </div>

      {/* Ticker Selector */}
      <Card>
        <div className="flex flex-wrap gap-2">
          {TICKERS.map((t) => (
            <button
              key={t}
              onClick={() => setTicker(t)}
              className={clsx(
                "px-3 py-1 rounded-md text-sm font-medium transition",
                ticker === t
                  ? "bg-blue-600 text-white"
                  : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
              )}
            >
              {t}
            </button>
          ))}
        </div>
      </Card>

      {/* Sentiment Trend */}
      <Card>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">
            Sentiment Trend — {ticker}
          </h2>

          {/* Range Selector */}
          <div className="flex gap-2">
            {RANGES.map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={clsx(
                  "px-3 py-1 rounded-md text-sm font-medium transition",
                  range === r
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                )}
              >
                {r}
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : trendData.length > 0 ? (
          <SentimentTrendChart data={trendData} range={range} />
        ) : (
          <p className="text-gray-500 text-center">No sentiment data available</p>
        )}
      </Card>

      {/* News Section */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Market News — {ticker}</h2>

        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage error={error} />
        ) : news.length === 0 ? (
          <p className="text-gray-500 text-center">No news available</p>
        ) : (
          <div className="space-y-4">
            {news.map((item, index) => (
              <a
                key={index}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition"
              >
                <div className="flex justify-between items-start gap-3">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      {item.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {item.description}
                    </p>
                    <div className="text-xs text-gray-500 mt-2">
                      {item.source} • {item.publishedAt}
                    </div>
                  </div>
                  <span className={sentimentColor(item.sentiment)}>
                    {item.sentiment}
                  </span>
                </div>
              </a>
            ))}
          </div>
        )}
      </Card>

    </div>
  );
}