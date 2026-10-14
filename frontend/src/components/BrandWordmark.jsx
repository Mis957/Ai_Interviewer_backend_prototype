export default function BrandWordmark({ className = '', style = {}, swoopColor = 'currentColor', swoopHeight = 10, swoopBottom = -6, hideSwoop = false }) {
  return (
    <span className={`ps-wordmark-container ${className}`.trim()} style={style}>
      <span className="ps-wordmark">
        <span className="ps-deva">परि</span>Samvad
      </span>
      {!hideSwoop && (
        <svg
          className="ps-brand-swoop"
          viewBox="0 0 140 18"
          aria-hidden="true"
          preserveAspectRatio="none"
          style={{
            stroke: swoopColor,
            height: `${swoopHeight}px`,
            bottom: `${swoopBottom}px`,
          }}
        >
          <path d="M3 13c32-10 74-12 134 2M16 15c28-6 62-8 108-1" />
        </svg>
      )}
    </span>
  )
}
