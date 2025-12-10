import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Sparkles, RefreshCw } from 'lucide-react'
import { insightsAPI } from '../services/api'

export default function RiskStories({ ticker }) {
  const [generating, setGenerating] = useState(false)

  const { data, refetch, isLoading } = useQuery({
    queryKey: ['riskStory', ticker],
    queryFn: () => insightsAPI.generateRiskStory(ticker),
    enabled: false, // Manual trigger
  })

  const handleGenerate = async () => {
    setGenerating(true)
    await refetch()
    setGenerating(false)
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          <h2 className="text-xl font-bold text-white">AI Risk Story</h2>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating || isLoading}
          className="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded-lg text-sm flex items-center space-x-1 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`w-4 h-4 ${generating || isLoading ? 'animate-spin' : ''}`} />
          <span>Generate</span>
        </button>
      </div>

      <div className="space-y-4">
        {!data && !generating && (
          <div className="text-center py-12">
            <Sparkles className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">
              Click Generate to create an AI-powered risk narrative for {ticker}
            </p>
          </div>
        )}

        {(generating || isLoading) && (
          <div className="text-center py-12">
            <RefreshCw className="w-8 h-8 text-purple-500 animate-spin mx-auto mb-3" />
            <p className="text-slate-400 text-sm">Generating AI risk story...</p>
          </div>
        )}

        {data?.data && !generating && (
          <div className="space-y-4">
            {/* Risk Summary */}
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-white">{data.data.company_name}</h3>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  data.data.risk_data.risk_level === 'Low' ? 'bg-green-500/20 text-green-400' :
                  data.data.risk_data.risk_level === 'Medium' ? 'bg-yellow-500/20 text-yellow-400' :
                  data.data.risk_data.risk_level === 'High' ? 'bg-orange-500/20 text-orange-400' :
                  'bg-red-500/20 text-red-400'
                }`}>
                  {data.data.risk_data.risk_level} Risk
                </span>
              </div>
              <p className="text-3xl font-bold text-yellow-400">
                {data.data.risk_data.overall_risk_score.toFixed(1)}/10
              </p>
            </div>

            {/* AI Generated Story */}
            <div className="prose prose-invert prose-sm max-w-none">
              <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {data.data.story}
              </div>
            </div>

            {/* Risk Components */}
            <div className="border-t border-slate-700 pt-4 mt-4">
              <p className="text-xs text-slate-400 mb-3 uppercase tracking-wide">Risk Factors</p>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(data.data.risk_data.components).map(([key, value]) => (
                  <div key={key} className="bg-slate-700/30 rounded px-3 py-2">
                    <p className="text-xs text-slate-400 capitalize">
                      {key.replace('_score', '').replace('_', ' ')}
                    </p>
                    <p className="text-sm font-bold text-white">{value.toFixed(1)}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
