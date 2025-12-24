import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../services/api'
import type { Flip } from '../services/api'
import './ListItem.css'

interface ListingSuggestion {
  flip_id: number
  suggested_title: string
  description: string
  ebay_category: { category_id: number; category_name: string; category_key: string }
  testing_checklist: string[]
}

export default function ListItem() {
  const { flipId } = useParams<{ flipId: string }>()
  const navigate = useNavigate()

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [suggestion, setSuggestion] = useState<ListingSuggestion | null>(null)
  const [flip, setFlip] = useState<Flip | null>(null)

  // Form state
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [price, setPrice] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [categoryName, setCategoryName] = useState('')
  const [images, setImages] = useState<File[]>([])
  const [imagePreviews, setImagePreviews] = useState<string[]>([])

  useEffect(() => {
    if (flipId) loadData()
  }, [flipId])

  const loadData = async () => {
    if (!flipId) return

    try {
      setLoading(true)
      // Load flip and suggestion in parallel
      const [flipsData, suggestionData] = await Promise.all([
        api.getFlips(),
        api.getFlipListingSuggestion(parseInt(flipId))
      ])

      const currentFlip = flipsData.find(f => f.id === parseInt(flipId))
      if (!currentFlip) {
        throw new Error('Flip not found')
      }

      setFlip(currentFlip)
      setSuggestion(suggestionData)
      setTitle(suggestionData.suggested_title)
      setDescription(suggestionData.description)
      setCategoryId(suggestionData.ebay_category.category_id.toString())
      setCategoryName(suggestionData.ebay_category.category_name)
    } catch (error) {
      console.error('Failed to load listing data:', error)
      alert('Failed to load listing details')
    } finally {
      setLoading(false)
    }
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    const newFiles = Array.from(files)
    const totalImages = images.length + newFiles.length

    if (totalImages > 12) {
      alert('Maximum 12 photos allowed')
      return
    }

    setImages(prev => [...prev, ...newFiles])

    // Create preview URLs
    newFiles.forEach(file => {
      const reader = new FileReader()
      reader.onloadend = () => {
        setImagePreviews(prev => [...prev, reader.result as string])
      }
      reader.readAsDataURL(file)
    })
  }

  const removeImage = (index: number) => {
    setImages(prev => prev.filter((_, i) => i !== index))
    setImagePreviews(prev => prev.filter((_, i) => i !== index))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!flipId) return
    if (!title.trim()) {
      alert('Please enter a title')
      return
    }
    if (!price.trim() || isNaN(parseFloat(price))) {
      alert('Please enter a valid price')
      return
    }
    if (images.length === 0) {
      alert('Please add at least one photo')
      return
    }

    setSubmitting(true)

    try {
      // TODO: Upload images to eBay first
      // For now, we'll create the listing with placeholder URLs
      const result = await api.createEbayListing(parseInt(flipId), {
        title: title.trim(),
        description: description.trim(),
        category_id: categoryId,
        price: parseFloat(price),
        condition: 'used',
        image_urls: imagePreviews, // These would need to be uploaded first
      })

      if (result.success) {
        alert(`Your item is now live on eBay!\n\n${result.ebay_url}`)
        navigate('/flips')
      } else {
        if (result.requires_manual_listing) {
          alert(result.error || 'Please complete the listing manually on eBay')
        } else {
          alert(result.error || 'Failed to create listing')
        }
      }
    } catch (error) {
      console.error('Listing error:', error)
      alert('Failed to create listing. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="list-item loading">
        <div className="loading-spinner"></div>
        <p>Loading listing details...</p>
      </div>
    )
  }

  if (!flip || !suggestion) {
    return (
      <div className="list-item error">
        <p>Failed to load listing details</p>
        <button onClick={() => navigate('/flips')}>Back to Flips</button>
      </div>
    )
  }

  return (
    <div className="list-item">
      <header className="list-header">
        <button className="back-btn" onClick={() => navigate('/flips')}>
          Back
        </button>
        <div className="header-text">
          <h1>List on eBay</h1>
          <p className="item-name">{flip.item_name}</p>
        </div>
      </header>

      <form className="list-form" onSubmit={handleSubmit}>
        {/* Photos Section */}
        <section className="form-section">
          <h2 className="section-title">Photos ({images.length}/12)</h2>
          <p className="section-hint">Add up to 12 photos. First photo is the main image.</p>

          <div className="images-container">
            {/* Add Photo Button */}
            <label className="add-photo-btn">
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageChange}
                style={{ display: 'none' }}
              />
              <span className="add-icon">+</span>
              <span className="add-text">Add Photos</span>
            </label>

            {/* Selected Images */}
            {imagePreviews.map((preview, index) => (
              <div key={index} className="image-preview">
                <img src={preview} alt={`Preview ${index + 1}`} />
                {index === 0 && (
                  <div className="main-badge">MAIN</div>
                )}
                <button
                  type="button"
                  className="remove-btn"
                  onClick={() => removeImage(index)}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </section>

        {/* Category */}
        <section className="form-section">
          <h2 className="section-title">Category</h2>
          <div className="category-box">
            {categoryName}
          </div>
        </section>

        {/* Title */}
        <section className="form-section">
          <h2 className="section-title">Title</h2>
          <input
            type="text"
            className="input"
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="Enter listing title"
            maxLength={80}
          />
          <p className="char-count">{title.length}/80 characters</p>
        </section>

        {/* Price */}
        <section className="form-section">
          <h2 className="section-title">Price</h2>
          <div className="price-input-container">
            <span className="price-currency">$</span>
            <input
              type="number"
              className="price-input"
              value={price}
              onChange={e => setPrice(e.target.value)}
              placeholder="0.00"
              step="0.01"
              min="0"
            />
          </div>
        </section>

        {/* Description */}
        <section className="form-section">
          <h2 className="section-title">Description</h2>
          <textarea
            className="textarea"
            value={description}
            onChange={e => setDescription(e.target.value)}
            placeholder="Enter listing description"
            rows={8}
          />
        </section>

        {/* Testing Checklist */}
        {suggestion.testing_checklist && suggestion.testing_checklist.length > 0 && (
          <section className="form-section">
            <h2 className="section-title">Testing Checklist</h2>
            <p className="section-hint">Make sure you've tested these before listing:</p>
            <div className="checklist">
              {suggestion.testing_checklist.map((item, index) => (
                <div key={index} className="checklist-item">
                  <span className="checkbox">☐</span>
                  <span className="checklist-text">{item}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          className={`submit-btn ${submitting || images.length === 0 ? 'disabled' : ''}`}
          disabled={submitting || images.length === 0}
        >
          {submitting ? (
            <>
              <span className="loading-spinner small"></span>
              Creating Listing...
            </>
          ) : images.length === 0 ? (
            'Add Photos to List'
          ) : (
            'List on eBay'
          )}
        </button>
      </form>
    </div>
  )
}
