import { useEffect, useState } from "react";
import { Card } from "../components/common/Card";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorMessage } from "../components/common/ErrorMessage";
import SentimentTrendChart from "../components/charts/SentimentTrendChart";
import clsx from "clsx";

/* ---------------- TYPES ---------------- */

interface NewsItem {
  title: string;
  description: string;
  url: string;
  source: string;
  publishedAt: string;
  sentiment: "positive" | "negative" | "neutral";
}

interface SentimentData {
  date: string;
  sentimentScore: number; // -1 to +1
}

/* ---------------- MOCK API (REPLACE LATER) ---------------- */

const fetchNews = async (): Promise<NewsItem[]> => {
  return [
    {
      title: "Apple stock rises after strong earnings",
      description: "Apple reported better-than-expected quarterly results...",
      url: "#",
      source: "Reuters",
      publishedAt: "2 hours ago",
      sentiment: "positive",
    },
    {
      title: "Tesla faces production challenges",
      description: "Supply chain disruptions impact Tesla output...",
      url: "#",
      source: "Bloomberg",
      publishedAt: "5 hours ago",
      sentiment: "negative",
    },
    {
      title: "Market remains stable amid global uncertainty",
      description: "Investors remain cautious as global trends evolve...",
      url: "#",
      source: "CNBC",
      publishedAt: "1 day ago",
      sentiment: "neutral",
    },
  ];
};

/* ---------------- TREND GENERATOR ---------------- */

const generateSentimentTrend = (): SentimentData[] => {
  return [
    { date: "Mon", sentimentScore: 0.3 },
    { date: "Tue", sentimentScore: -0.2 },
    { date: "Wed", sentimentScore: 0.5 },
    { date: "Thu", sentimentScore: 0.1 },
    { date: "Fri", sentimentScore: 0.7 },
    { date: "Sat", sentimentScore: -0.1 },
    { date: "Sun", sentimentScore: 0.4 },
  ];
};

/* ---------------- COMPONENT ---------------- */

export default function Analytics() {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [trendData, setTrendData] = useState<SentimentData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);

        const newsData = await fetchNews();
        setNews(newsData);

        const trend = generateSentimentTrend();
        setTrendData(trend);

      } catch (err) {
        setError("Failed to load analytics data");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  /* ---------------- HELPERS ---------------- */

  const sentimentColor = (sentiment: string) =>
    clsx(
      "px-2 py-1 text-xs rounded-full font-semibold",
      sentiment === "positive" && "bg-green-100 text-green-700",
      sentiment === "negative" && "bg-red-100 text-red-700",
      sentiment === "neutral" && "bg-gray-100 text-gray-700"
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
          News insights and sentiment trends
        </p>
      </div>

      {/* Sentiment Trend Chart */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">
          Sentiment Trend (Last 7 Days)
        </h2>

        {trendData.length > 0 ? (
          <SentimentTrendChart data={trendData} />
        ) : (
          <p className="text-gray-500 text-center">
            No sentiment data available
          </p>
        )}
      </Card>

      {/* News Section */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Market News</h2>

        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage error={error} />
        ) : news.length === 0 ? (
          <p className="text-gray-500 text-center">
            No news available
          </p>
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