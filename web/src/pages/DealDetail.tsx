import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, Deal, RepairOption } from '../services/api'
import './DealDetail.css'

export default function DealDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [deal, setDeal] = useState<Deal | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedRepairs, setSelectedRepairs] = useState<Set<string>>(new Set())
  const [showPurchaseModal, setShowPurchaseModal] = useState(false)
  const [buyPrice, setBuyPrice] = useState('')

  useEffect(() => {
    if (id) loadDeal(parseInt(id))
  }, [id])

  const loadDeal = async (dealId: number) => {
    try {
      setLoading(true)
      const data = await api.getDeal(dealId)
      setDeal(data)
      if (data.asking_price) setBuyPrice(data.asking_price.toString())
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleConditionChange = async (condition: 'new' | 'used' | 'needs_repair') => {
    if (!deal) return
    try {
      const updated = await api.updateCondition(deal.id, condition)
      setDeal(updated)
    } catch (err) {
      console.error(err)
    }
  }

  const handleDismiss = async () => {
    if (!deal) return
    if (!confirm('Dismiss this deal?')) return
    try {
      await api.dismissDeal(deal.id)
      navigate('/deals')
    } catch (err) {
      console.error(err)
    }
  }

  const handlePurchase = async () => {
    if (!deal || !buyPrice) return
    try {
      const repairs = deal.repair_options?.filter(r => selectedRepairs.has(r.id)) || []
      await api.purchaseDeal(deal.id, {
        buy_price: parseFloat(buyPrice),
        buy_date: new Date().toISOString().split('T')[0],
        planned_repairs: repairs,
      })
      navigate('/flips')
    } catch (err) {
      console.error(err)
    }
  }

  const toggleRepair = (repairId: string) => {
    setSelectedRepairs(prev => {
      const next = new Set(prev)
      if (next.has(repairId)) next.delete(repairId)
      else next.add(repairId)
      return next
    })
  }

  const calculateTotalRepairCost = () => {
    if (!deal?.repair_options) return 0
    return deal.repair_options
      .filter(r => selectedRepairs.has(r.id))
      .reduce((sum, r) => sum + r.part_cost + (r.labor_hours * 25), 0)
  }

  const formatPrice = (price: number | null) => {
    if (price === null) return '—'
    return `$${price.toFixed(2)}`
  }

  if (loading) return <div className="deal-detail loading">Loading...</div>
  if (!deal) return <div className="deal-detail error">Deal not found</div>

  const repairCost = calculateTotalRepairCost()
  const projectedProfit = deal.market_value && deal.asking_price
    ? deal.market_value - deal.asking_price - repairCost - (deal.market_value * 0.13)
    : null

  return (
    <div className="deal-detail">
      <header className="detail-header">
        <button className="back-btn" onClick={() => navigate('/deals')}>Back</button>
        <h1>{deal.title}</h1>
      </header>

      <div className="detail-content">
        <div className="image-section">
          {deal.image_url ? (
            <img src={deal.image_url} alt={deal.title} className="main-image" />
          ) : (
            <div className="no-image">No Image</div>
          )}
        </div>

        <div className="info-section">
          <div className="price-card">
            <div className="price-row">
              <span>Asking Price:</span>
              <span className="asking">{formatPrice(deal.asking_price)}</span>
            </div>
            <div className="price-row">
              <span>Market Value:</span>
              <span className="market">{formatPrice(deal.market_value)}</span>
            </div>
            {repairCost > 0 && (
              <div className="price-row">
                <span>Repair Cost:</span>
                <span className="repair">-{formatPrice(repairCost)}</span>
              </div>
            )}
            <div className="price-row profit">
              <span>Est. Profit:</span>
              <span className={projectedProfit && projectedProfit > 0 ? 'positive' : 'negative'}>
                {formatPrice(projectedProfit)}
              </span>
            </div>
          </div>

          <div className="condition-section">
            <h3>Condition</h3>
            <div className="condition-buttons">
              {(['new', 'used', 'needs_repair'] as const).map(cond => (
                <button
                  key={cond}
                  className={`condition-btn ${deal.condition === cond ? 'active' : ''}`}
                  onClick={() => handleConditionChange(cond)}
                >
                  {cond === 'needs_repair' ? 'Repair' : cond.charAt(0).toUpperCase() + cond.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {deal.repair_options && deal.repair_options.length > 0 && (
            <div className="repair-section">
              <h3>Repair Options</h3>
              {deal.repair_options.map(repair => (
                <div
                  key={repair.id}
                  className={`repair-option ${selectedRepairs.has(repair.id) ? 'selected' : ''}`}
                  onClick={() => toggleRepair(repair.id)}
                >
                  <div className="repair-header">
                    <span className="checkbox">{selectedRepairs.has(repair.id) ? '✓' : ''}</span>
                    <span className="repair-name">{repair.name}</span>
                  </div>
                  <div className="repair-cost">
                    <span>Parts: {formatPrice(repair.part_cost)}</span>
                    <span>Labor: {repair.labor_hours}h (~${repair.labor_hours * 25})</span>
                  </div>
                  {repair.part_url && (
                    <a href={repair.part_url} target="_blank" rel="noopener" className="part-link">
                      View Part
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="details-section">
            <h3>Details</h3>
            <div className="detail-row"><span>Source:</span><span>{deal.source || '—'}</span></div>
            <div className="detail-row"><span>Category:</span><span>{deal.category || '—'}</span></div>
            <div className="detail-row"><span>Brand:</span><span>{deal.brand || '—'}</span></div>
            <div className="detail-row"><span>Model:</span><span>{deal.model || '—'}</span></div>
            {deal.local_pickup_available && (
              <div className="detail-row">
                <span>Location:</span>
                <span>{deal.location} ({deal.distance_miles?.toFixed(1)} mi)</span>
              </div>
            )}
          </div>

          <div className="action-buttons">
            <button className="btn-primary" onClick={() => setShowPurchaseModal(true)}>
              Mark as Purchased
            </button>
            {deal.listing_url && (
              <a href={deal.listing_url} target="_blank" rel="noopener" className="btn-secondary">
                View Listing
              </a>
            )}
            <button className="btn-danger" onClick={handleDismiss}>Dismiss</button>
          </div>
        </div>
      </div>

      {showPurchaseModal && (
        <div className="modal-overlay" onClick={() => setShowPurchaseModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h2>Mark as Purchased</h2>
            <div className="form-group">
              <label>Purchase Price</label>
              <input
                type="number"
                value={buyPrice}
                onChange={e => setBuyPrice(e.target.value)}
                placeholder="0.00"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowPurchaseModal(false)}>
                Cancel
              </button>
              <button className="btn-primary" onClick={handlePurchase}>
                Confirm Purchase
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
