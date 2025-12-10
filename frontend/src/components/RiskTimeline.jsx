import { useQuery } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { riskAPI } from '../services/api'

export default function RiskTimeline({ ticker }) {
  const { data, isLoading } = useQuery({
    queryKey: ['riskTimeline', ticker],
    queryFn: () => riskAPI.getRiskTimeline(ticker, 90),
    enabled: !!ticker,
  })

  const timelineData = data?.data?.timeline || []

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold">{data.date}</p>
          <p className="text-yellow-400">Risk Score: {data.overall_risk_score?.toFixed(2)}</p>
          <p className="text-blue-400">Volatility: {data.volatility_score?.toFixed(2)}</p>
          <p className="text-purple-400">Sentiment: {data.sentiment_score?.toFixed(2)}</p>
        </div>
      )
    }
    return null
  }

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <h2 className="text-xl font-bold text-white mb-4">Risk Score Timeline</h2>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-400">Loading timeline data...</div>
        </div>
      ) : timelineData.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-slate-400">No historical risk data available</div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={timelineData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="date"
              stroke="#94a3b8"
              tick={{ fill: '#94a3b8' }}
            />
            <YAxis
              stroke="#94a3b8"
              tick={{ fill: '#94a3b8' }}
              domain={[0, 10]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />

            {/* Risk threshold lines */}
            <ReferenceLine y={3} stroke="#10b981" strokeDasharray="3 3" label="Low" />
            <ReferenceLine y={6} stroke="#f59e0b" strokeDasharray="3 3" label="Medium" />
            <ReferenceLine y={8} stroke="#ef4444" strokeDasharray="3 3" label="High" />

            <Line
              type="monotone"
              dataKey="overall_risk_score"
              stroke="#eab308"
              strokeWidth={3}
              dot={{ fill: '#eab308', r: 4 }}
              name="Overall Risk"
            />
            <Line
              type="monotone"
              dataKey="volatility_score"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              name="Volatility"
            />
            <Line
              type="monotone"
              dataKey="sentiment_score"
              stroke="#a855f7"
              strokeWidth={2}
              dot={false}
              name="Sentiment"
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      {/* Risk Component Breakdown */}
      {timelineData.length > 0 && (
        <div className="mt-4 grid grid-cols-5 gap-2">
          <div className="bg-slate-700/50 rounded p-2 text-center">
            <p className="text-xs text-slate-400">Volatility</p>
            <p className="text-sm font-bold text-blue-400">
              {timelineData[0]?.volatility_score?.toFixed(1)}
            </p>
          </div>
          <div className="bg-slate-700/50 rounded p-2 text-center">
            <p className="text-xs text-slate-400">Litigation</p>
            <p className="text-sm font-bold text-red-400">
              {timelineData[0]?.litigation_score?.toFixed(1)}
            </p>
          </div>
          <div className="bg-slate-700/50 rounded p-2 text-center">
            <p className="text-xs text-slate-400">Sentiment</p>
            <p className="text-sm font-bold text-purple-400">
              {timelineData[0]?.sentiment_score?.toFixed(1)}
            </p>
          </div>
          <div className="bg-slate-700/50 rounded p-2 text-center">
            <p className="text-xs text-slate-400">Financial</p>
            <p className="text-sm font-bold text-orange-400">
              {timelineData[0]?.financial_anomaly_score?.toFixed(1)}
            </p>
          </div>
          <div className="bg-slate-700/50 rounded p-2 text-center">
            <p className="text-xs text-slate-400">Regulatory</p>
            <p className="text-sm font-bold text-green-400">
              {timelineData[0]?.regulatory_score?.toFixed(1)}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
