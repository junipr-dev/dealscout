import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, Deal } from '../services/api'
import './Deals.css'

type FilterTab = 'good' | 'review' | 'all'

export default function Deals() {
  const navigate = useNavigate()
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<FilterTab>('good')

  useEffect(() => {
    loadDeals()
  }, [activeTab])

  const loadDeals = async () => {
    try {
      setLoading(true)
      let params: any = {}

      if (activeTab === 'good') {
        params.status = 'new'
      } else if (activeTab === 'review') {
        params.needs_review = true
      }

      const data = await api.getDeals(params)
      setDeals(data)
    } catch (err) {
      setError('Failed to load deals')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const formatPrice = (price: number | null) => {
    if (price === null) return '—'
    return `$${price.toFixed(0)}`
  }

  const getProfitClass = (profit: number | null) => {
    if (profit === null) return ''
    if (profit >= 50) return 'profit-high'
    if (profit >= 20) return 'profit-medium'
    return 'profit-low'
  }

  const getConditionBadge = (condition: string | null) => {
    if (!condition) return null
    const badges: Record<string, { text: string; className: string }> = {
      'new': { text: 'New', className: 'badge-new' },
      'used': { text: 'Used', className: 'badge-used' },
      'needs_repair': { text: 'Needs Repair', className: 'badge-repair' },
      'unknown': { text: 'Unknown', className: 'badge-unknown' },
    }
    return badges[condition] || null
  }

  if (loading) {
    return (
      <div className="deals-page">
        <div className="loading">Loading deals...</div>
      </div>
    )
  }

  return (
    <div className="deals-page">
      <header className="page-header">
        <h1>Deals</h1>
      </header>

      <div className="filter-tabs">
        <button
          className={`tab ${activeTab === 'good' ? 'active' : ''}`}
          onClick={() => setActiveTab('good')}
        >
          Good Deals
        </button>
        <button
          className={`tab ${activeTab === 'review' ? 'active' : ''}`}
          onClick={() => setActiveTab('review')}
        >
          Needs Review
        </button>
        <button
          className={`tab ${activeTab === 'all' ? 'active' : ''}`}
          onClick={() => setActiveTab('all')}
        >
          All
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="deals-grid">
        {deals.length === 0 ? (
          <div className="empty-state">
            <p>No deals found</p>
          </div>
        ) : (
          deals.map(deal => {
            const conditionBadge = getConditionBadge(deal.condition)
            const isRepair = deal.condition === 'needs_repair'

            return (
              <div
                key={deal.id}
                className={`deal-card ${isRepair ? 'repair-card' : ''}`}
                onClick={() => navigate(`/deals/${deal.id}`)}
              >
                <div className="deal-image">
                  {deal.image_url ? (
                    <img src={deal.image_url} alt={deal.title} />
                  ) : (
                    <div className="no-image">No Image</div>
                  )}
                  {conditionBadge && (
                    <span className={`condition-badge ${conditionBadge.className}`}>
                      {conditionBadge.text}
                    </span>
                  )}
                </div>

                <div className="deal-info">
                  <h3 className="deal-title">{deal.title}</h3>

                  <div className="deal-meta">
                    {deal.category && <span className="category">{deal.category}</span>}
                    {deal.source && <span className="source">{deal.source}</span>}
                  </div>

                  <div className="deal-prices">
                    <div className="price-row">
                      <span className="label">Asking:</span>
                      <span className="asking-price">{formatPrice(deal.asking_price)}</span>
                    </div>
                    <div className="price-row">
                      <span className="label">Market:</span>
                      <span className="market-price">{formatPrice(deal.market_value)}</span>
                    </div>
                    <div className="price-row profit-row">
                      <span className="label">Profit:</span>
                      <span className={`profit-value ${getProfitClass(deal.estimated_profit)}`}>
                        {formatPrice(deal.estimated_profit)}
                      </span>
                    </div>
                  </div>

                  {deal.local_pickup_available && (
                    <div className="local-pickup">
                      Local Pickup {deal.distance_miles && `(${deal.distance_miles.toFixed(1)} mi)`}
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
