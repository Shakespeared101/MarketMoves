import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-react'
import { marketAPI, riskAPI } from '../services/api'
import RiskTimeline from './RiskTimeline'
import RiskStories from './RiskStories'

export default function Dashboard() {
  const [selectedTicker, setSelectedTicker] = useState('AAPL')

  const { data: companies } = useQuery({
    queryKey: ['companies'],
    queryFn: () => marketAPI.getCompanies(),
  })

  const { data: riskData, isLoading: riskLoading } = useQuery({
    queryKey: ['risk', selectedTicker],
    queryFn: () => riskAPI.getRiskScore(selectedTicker),
    enabled: !!selectedTicker,
  })

  const { data: priceData } = useQuery({
    queryKey: ['prices', selectedTicker],
    queryFn: () => marketAPI.getLatestPrice(selectedTicker),
    enabled: !!selectedTicker,
  })

  const getRiskColor = (score) => {
    if (score < 3) return 'text-risk-low'
    if (score < 6) return 'text-risk-medium'
    if (score < 8) return 'text-risk-high'
    return 'text-risk-critical'
  }

  const getRiskBgColor = (score) => {
    if (score < 3) return 'bg-risk-low/20'
    if (score < 6) return 'bg-risk-medium/20'
    if (score < 8) return 'bg-risk-high/20'
    return 'bg-risk-critical/20'
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <BarChart3 className="w-8 h-8 text-blue-500" />
              <h1 className="text-2xl font-bold text-white">MarketMoves</h1>
              <span className="text-sm text-slate-400">Risk Intelligence Dashboard</span>
            </div>

            {/* Ticker Selector */}
            <select
              value={selectedTicker}
              onChange={(e) => setSelectedTicker(e.target.value)}
              className="bg-slate-700 text-white px-4 py-2 rounded-lg border border-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {companies?.data?.companies?.map((company) => (
                <option key={company.ticker} value={company.ticker}>
                  {company.ticker} - {company.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* Risk Score Card */}
          <div className={`bg-slate-800 rounded-lg p-6 border border-slate-700 ${getRiskBgColor(riskData?.data?.overall_risk_score || 0)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Overall Risk Score</p>
                <p className={`text-3xl font-bold ${getRiskColor(riskData?.data?.overall_risk_score || 0)}`}>
                  {riskLoading ? '...' : riskData?.data?.overall_risk_score?.toFixed(1) || 'N/A'}
                </p>
                <p className="text-sm text-slate-400 mt-1">
                  {riskData?.data?.risk_level || 'Unknown'}
                </p>
              </div>
              <AlertTriangle className={`w-10 h-10 ${getRiskColor(riskData?.data?.overall_risk_score || 0)}`} />
            </div>
          </div>

          {/* Price Card */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-slate-400 text-sm">Current Price</p>
                <p className="text-3xl font-bold text-white">
                  ${priceData?.data?.price?.toFixed(2) || 'N/A'}
                </p>
                <p className={`text-sm flex items-center mt-1 ${
                  (priceData?.data?.change || 0) >= 0 ? 'text-green-500' : 'text-red-500'
                }`}>
                  {(priceData?.data?.change || 0) >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
                  {priceData?.data?.change_percent?.toFixed(2)}%
                </p>
              </div>
            </div>
          </div>

          {/* Volatility Score */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <p className="text-slate-400 text-sm">Volatility Risk</p>
            <p className="text-3xl font-bold text-orange-500">
              {riskData?.data?.components?.volatility_score?.toFixed(1) || 'N/A'}
            </p>
            <p className="text-sm text-slate-400 mt-1">Market Movement</p>
          </div>

          {/* Sentiment Score */}
          <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
            <p className="text-slate-400 text-sm">Sentiment Risk</p>
            <p className="text-3xl font-bold text-purple-500">
              {riskData?.data?.components?.sentiment_score?.toFixed(1) || 'N/A'}
            </p>
            <p className="text-sm text-slate-400 mt-1">News Sentiment</p>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Risk Timeline - Takes 2 columns */}
          <div className="lg:col-span-2">
            <RiskTimeline ticker={selectedTicker} />
          </div>

          {/* Risk Stories - Takes 1 column */}
          <div className="lg:col-span-1">
            <RiskStories ticker={selectedTicker} />
          </div>
        </div>
      </div>
    </div>
  )
}
