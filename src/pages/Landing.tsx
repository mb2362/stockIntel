import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, BarChart3, Bell, Shield, Zap, LineChart } from 'lucide-react';
import { Button } from '../components/common/Button';
import { useEffect, useState } from 'react';

export default function Landing() {
    const navigate = useNavigate();
    const [typedText, setTypedText] = useState('');
    const [isTypingComplete, setIsTypingComplete] = useState(false);
    const fullText = 'Real-Time Intelligence';

    // Typewriter effect
    useEffect(() => {
        let currentIndex = 0;
        const interval = setInterval(() => {
            if (currentIndex <= fullText.length) {
                setTypedText(fullText.slice(0, currentIndex));
                currentIndex++;
            } else {
                clearInterval(interval);
                setIsTypingComplete(true); // Hide cursor when typing is done
            }
        }, 100); // Speed of typing (100ms per character)

        return () => clearInterval(interval);
    }, []);

    const fadeInUp = {
        initial: { opacity: 0, y: 60 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.6 }
    };

    const staggerContainer = {
        animate: {
            transition: {
                staggerChildren: 0.1
            }
        }
    };

    const features = [
        {
            icon: TrendingUp,
            title: 'Real-Time Market Data',
            description: 'Get live stock prices, market indices, and trending stocks updated every 30 seconds.',
            color: 'text-blue-500'
        },
        {
            icon: BarChart3,
            title: 'Advanced Analytics',
            description: 'Analyze stocks with technical indicators including MA, RSI, MACD, and more.',
            color: 'text-green-500'
        },
        {
            icon: Bell,
            title: 'Smart Watchlist',
            description: 'Track your favorite stocks in one place with automatic price updates.',
            color: 'text-purple-500'
        },
        {
            icon: Shield,
            title: 'Secure & Reliable',
            description: 'Enterprise-grade security with 99.9% uptime guarantee.',
            color: 'text-red-500'
        },
        {
            icon: Zap,
            title: 'Lightning Fast',
            description: 'Optimized performance with instant search and smooth navigation.',
            color: 'text-yellow-500'
        },
        {
            icon: LineChart,
            title: 'Stock Comparison',
            description: 'Compare multiple stocks side-by-side to make informed decisions.',
            color: 'text-indigo-500'
        }
    ];

    const stats = [
        { value: '1K+', label: 'Active Users' },
        { value: '50K+', label: 'Stocks Tracked' },
        { value: '99.9%', label: 'Uptime' },
        { value: '24/7', label: 'Support' }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
            {/* Hero Section */}
            <section className="relative overflow-hidden pt-20 pb-32 px-4">
                {/* Animated Background Elements */}
                <div className="absolute inset-0 overflow-hidden">
                    <motion.div
                        className="absolute top-20 left-10 w-72 h-72 bg-primary-500/10 rounded-full blur-3xl"
                        animate={{
                            scale: [1, 1.2, 1],
                            opacity: [0.3, 0.5, 0.3],
                        }}
                        transition={{
                            duration: 8,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    />
                    <motion.div
                        className="absolute bottom-20 right-10 w-96 h-96 bg-success-500/10 rounded-full blur-3xl"
                        animate={{
                            scale: [1.2, 1, 1.2],
                            opacity: [0.5, 0.3, 0.5],
                        }}
                        transition={{
                            duration: 10,
                            repeat: Infinity,
                            ease: "easeInOut"
                        }}
                    />
                </div>

                <div className="container mx-auto max-w-6xl relative z-10">
                    <motion.div
                        className="text-center"
                        initial="initial"
                        animate="animate"
                        variants={staggerContainer}
                    >
                        <motion.div variants={fadeInUp}>
                            <span className="inline-block px-4 py-2 mb-6 text-sm font-semibold text-primary-600 dark:text-primary-400 bg-primary-100 dark:bg-primary-900/30 rounded-full">
                                🚀 Your Smart Investment Companion
                            </span>
                        </motion.div>

                        <motion.h1
                            className="text-5xl md:text-7xl font-bold text-gray-900 dark:text-white mb-6"
                            variants={fadeInUp}
                        >
                            Master the Market with
                            <br />
                            <span className="bg-gradient-to-r from-primary-600 to-success-600 bg-clip-text text-transparent block overflow-visible pb-2">
                                {typedText}
                                {!isTypingComplete && (
                                    <motion.span
                                        className="inline-block w-1 h-12 md:h-16 ml-2 bg-gradient-to-r from-primary-600 to-success-600 align-middle"
                                        animate={{ opacity: [1, 0] }}
                                        transition={{ duration: 0.8, repeat: Infinity, repeatType: "reverse" }}
                                    />
                                )}
                            </span>
                        </motion.h1>

                        <motion.p
                            className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-10 max-w-3xl mx-auto"
                            variants={fadeInUp}
                        >
                            Track stocks, analyze trends, and make informed investment decisions with our powerful analytics platform.
                        </motion.p>

                        <motion.div
                            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
                            variants={fadeInUp}
                        >
                            <Button
                                size="lg"
                                onClick={() => navigate('/dashboard')}
                                className="text-lg px-8 py-4"
                            >
                                Get Started Free
                            </Button>
                            <Button
                                size="lg"
                                variant="secondary"
                                onClick={() => navigate('/dashboard')}
                                className="text-lg px-8 py-4"
                            >
                                View Demo
                            </Button>
                        </motion.div>

                        {/* Animated Stats */}
                        <motion.div
                            className="grid grid-cols-2 md:grid-cols-4 gap-8 mt-20"
                            variants={fadeInUp}
                        >
                            {stats.map((stat, index) => (
                                <motion.div
                                    key={stat.label}
                                    className="text-center"
                                    initial={{ opacity: 0, scale: 0.5 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    transition={{ delay: 0.8 + index * 0.1, duration: 0.5 }}
                                >
                                    <div className="text-4xl md:text-5xl font-bold text-primary-600 dark:text-primary-400 mb-2">
                                        {stat.value}
                                    </div>
                                    <div className="text-gray-600 dark:text-gray-400">
                                        {stat.label}
                                    </div>
                                </motion.div>
                            ))}
                        </motion.div>
                    </motion.div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 px-4 bg-white dark:bg-gray-800">
                <div className="container mx-auto max-w-6xl">
                    <motion.div
                        className="text-center mb-16"
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                    >
                        <h2 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
                            Powerful Features
                        </h2>
                        <p className="text-xl text-gray-600 dark:text-gray-300">
                            Everything you need to make smarter investment decisions
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {features.map((feature, index) => (
                            <motion.div
                                key={feature.title}
                                className="bg-gray-50 dark:bg-gray-900 rounded-2xl p-8 hover:shadow-2xl transition-all"
                                initial={{ opacity: 0, y: 50 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: index * 0.1, duration: 0.5 }}
                                whileHover={{ scale: 1.05, y: -10 }}
                            >
                                <div className={`w-14 h-14 ${feature.color} bg-opacity-10 rounded-xl flex items-center justify-center mb-6`}>
                                    <feature.icon className={`w-7 h-7 ${feature.color}`} />
                                </div>
                                <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
                                    {feature.title}
                                </h3>
                                <p className="text-gray-600 dark:text-gray-400">
                                    {feature.description}
                                </p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-20 px-4 bg-gradient-to-r from-primary-600 to-success-600">
                <div className="container mx-auto max-w-4xl text-center">
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                    >
                        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
                            Ready to Start Trading Smarter?
                        </h2>
                        <p className="text-xl text-white/90 mb-10">
                            Join thousands of investors making data-driven decisions every day.
                        </p>
                        <Button
                            size="lg"
                            onClick={() => navigate('/dashboard')}
                            className="text-primary-600 hover:bg-white-100 text-lg px-8 py-4"
                        >
                            Launch Dashboard
                        </Button>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-4 bg-gray-900 text-gray-400">
                <div className="container mx-auto max-w-6xl text-center">
                    <p className="mb-4">© 2026 Stock Market Intelligence Platform. All rights reserved.</p>
                    <p className="text-sm">Built with React, TypeScript, and Tailwind CSS</p>
                </div>
            </footer>
        </div>
    );
}
