export default function HandwrittenHighlight({
  children,
  className = '',
  color = '#080808',
  swoopColor = '#080808',
  size = '34px',
  rotate = '-4deg',
  underlineOffset = '-4px',
  swoopWidth = '68%',
  strokeWidth = 2.4,
}) {
  return (
    <span
      className={`script-highlight ${className}`.trim()}
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        position: 'relative',
        transform: `rotate(${rotate})`,
        transformOrigin: 'left center',
        verticalAlign: 'middle',
        margin: '0 0 6px',
      }}
    >
      <span
        className="script-text"
        style={{
          fontFamily: 'Caveat, cursive',
          fontSize: size,
          lineHeight: 1,
          color,
          fontWeight: 400,
          letterSpacing: 'normal',
          whiteSpace: 'nowrap',
        }}
      >
        {children}
      </span>
      <svg
        className="script-swoop-svg"
        viewBox="0 0 100 12"
        fill="none"
        aria-hidden="true"
        preserveAspectRatio="none"
        style={{
          width: swoopWidth,
          height: '7px',
          marginTop: underlineOffset,
          marginLeft: '4px',
          display: 'block',
          overflow: 'visible',
        }}
      >
        <path
          d="M2 8 C 28 2, 68 2, 98 7"
          stroke={swoopColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
      </svg>
    </span>
  )
}
