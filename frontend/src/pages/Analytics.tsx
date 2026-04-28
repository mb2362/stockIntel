import React, { useEffect, useState, useMemo } from "react";
import { Card } from "../components/common/Card";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorMessage } from "../components/common/ErrorMessage";
import SentimentTrendChart from "../components/charts/SentimentTrendChart";
import clsx from "clsx";

const TICKERS = [
    "NVDA", "AMZN", "AXON", "AAPL", "ORCL",
    "MSFT", "JPM",  "META", "TSLA", "AMD",
    "GOOGL","GOOG", "NFLX", "UBER", "CRM",
    "ADBE", "INTC", "QCOM", "MU",   "AVGO",
    "ARM",  "PANW", "SNOW", "PLTR", "SMCI",
    "GS",   "MS",   "BAC",  "V",    "MA",
    "BRK-B","UNH",  "LLY",  "JNJ",  "PFE",
    "XOM",  "CVX",  "COST", "WMT",  "TGT",
    "HD",   "LOW",  "DIS",  "PYPL", "XYZ",
    "COIN", "RIVN", "NIO",  "LCID", "SOFI",
];

const VISIBLE_COUNT = 10;
const RANGES = ["1D", "1W"] as const;
type Range = typeof RANGES[number];
const API_BASE = "http://localhost:8001/api/v1";

interface NewsItem {
    title: string;
    description: string;
    url: string;
    source: string;
    publishedAt: string;
    sentiment: "positive" | "negative" | "neutral";
    score: number;
}

interface SentimentData {
    date: string;
    sentimentScore: number;
}

function getRecommendation(news: NewsItem[]) {
    const hold = {
        label: "Hold",
        style: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
    };
    if (news.length === 0) return hold;
    const avg = news.reduce((sum, n) => sum + n.score, 0) / news.length;
    if (avg >= 0.3)  return { label: "Buy",  style: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" };
    if (avg <= -0.3) return { label: "Sell", style: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" };
    return hold;
}

function NewsCard({ item }: { item: NewsItem }) {
    const handleClick = () => {
        window.open(item.url, "_blank", "noopener,noreferrer");
    };

    const sentimentStyle = clsx(
        "px-2 py-1 text-xs rounded-full font-semibold shrink-0",
        item.sentiment === "positive" && "bg-green-100 text-green-700",
        item.sentiment === "negative" && "bg-red-100 text-red-700",
        item.sentiment === "neutral"  && "bg-gray-100 text-gray-700"
    );

    return (
        <div
            onClick={handleClick}
            className="block p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition cursor-pointer"
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
                <span className={sentimentStyle}>
                    {item.sentiment}
                </span>
            </div>
        </div>
    );
}

function NewsList({ news, loading, error }: { news: NewsItem[]; loading: boolean; error: string | null }) {
    if (loading) return <LoadingSpinner />;
    if (error)   return <ErrorMessage error={error} />;
    if (news.length === 0) return <p className="text-gray-500 text-center">No news available</p>;

    return (
        <div className="space-y-4">
            {news.map((item, index) => (
                <NewsCard key={index} item={item} />
            ))}
        </div>
    );
}

export default function Analytics() {
    const [ticker,    setTicker]    = useState("AAPL");
    const [range,     setRange]     = useState<Range>("1W");
    const [news,      setNews]      = useState<NewsItem[]>([]);
    const [trendData, setTrendData] = useState<SentimentData[]>([]);
    const [loading,   setLoading]   = useState(true);
    const [error,     setError]     = useState<string | null>(null);
    const [showAll,   setShowAll]   = useState(false);

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

    const visibleTickers = useMemo(
        () => (showAll ? TICKERS : TICKERS.slice(0, VISIBLE_COUNT)),
        [showAll]
    );

    const recommendation = useMemo(() => getRecommendation(news), [news]);

    return (
        <div className="space-y-6">

            <div>
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    Analytics Dashboard
                </h1>
                <p className="text-gray-600 dark:text-gray-400">
                    Live news insights and sentiment trends
                </p>
            </div>

            <Card>
                <div className="flex flex-wrap gap-2">
                    {visibleTickers.map((t) => (
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
                    <button
                        onClick={() => setShowAll((prev) => !prev)}
                        className="px-3 py-1 rounded-md text-sm font-medium transition bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/40 border border-blue-200 dark:border-blue-800"
                    >
                        {showAll ? "− Less" : `+ ${TICKERS.length - VISIBLE_COUNT} more`}
                    </button>
                </div>
            </Card>

            <Card>
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-xl font-semibold">Sentiment Trend — {ticker}</h2>
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
                    <SentimentTrendChart data={trendData} range={range as any} />
                ) : (
                    <p className="text-gray-500 text-center">No sentiment data available</p>
                )}
            </Card>

            <Card>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-xl font-semibold">Market News — {ticker}</h2>
                    {!loading && news.length > 0 && (
                        <span className={clsx("px-3 py-1 text-sm font-bold rounded-full", recommendation.style)}>
                            {recommendation.label}
                        </span>
                    )}
                </div>
                <NewsList news={news} loading={loading} error={error} />
            </Card>

        </div>
    );
}