import SwiftUI

// MARK: - Typography Tokens

/// Typography system using SF Pro (system font) per macOS HIG.
/// All styles use `Font.system()` to respect user accessibility settings.
enum Typography {
    // MARK: Display

    /// Large display text for hero sections (48pt, bold)
    static let heroTitle: Font = .system(size: 48, weight: .bold, design: .default)

    /// Page-level headers (28pt, semibold)
    static let pageTitle: Font = .system(size: 28, weight: .semibold, design: .default)

    /// Section headers within a page (20pt, semibold)
    static let sectionTitle: Font = .system(size: 20, weight: .semibold, design: .default)

    // MARK: Body

    /// Standard body copy (14pt, regular)
    static let bodyText: Font = .system(size: 14, weight: .regular, design: .default)

    /// Bold body variant for emphasis (14pt, semibold)
    static let bodyBold: Font = .system(size: 14, weight: .semibold, design: .default)

    /// Small body for secondary content (13pt, regular)
    static let bodySmall: Font = .system(size: 13, weight: .regular, design: .default)

    // MARK: Caption & Labels

    /// Caption text for metadata and labels (12pt, regular)
    static let captionText: Font = .system(size: 12, weight: .regular, design: .default)

    /// Small label text (11pt, medium)
    static let label: Font = .system(size: 11, weight: .medium, design: .default)

    // MARK: Monospace

    /// Monospaced text for code and script content (14pt, regular, monospaced)
    static let monospaceText: Font = .system(size: 14, weight: .regular, design: .monospaced)

    /// Small monospaced text for inline code (12pt, regular, monospaced)
    static let monospaceSmall: Font = .system(size: 12, weight: .regular, design: .monospaced)
}

// MARK: - Line Height Multipliers

extension Typography {
    /// Tight line height for display text (1.1×)
    static let lineHeightTight: CGFloat = 1.1

    /// Standard line height for body text (1.5×)
    static let lineHeightNormal: CGFloat = 1.5

    /// Relaxed line height for readable blocks (1.7×)
    static let lineHeightRelaxed: CGFloat = 1.7
}

// MARK: - Tracking (Letter Spacing)

extension Typography {
    /// Tight tracking for large display text (-0.5pt)
    static let trackingTight: CGFloat = -0.5

    /// Normal tracking for body text (0pt)
    static let trackingNormal: CGFloat = 0

    /// Wide tracking for labels and captions (0.3pt)
    static let trackingWide: CGFloat = 0.3
}

// MARK: - View Extensions

extension View {
    /// Apply hero title styling (48pt bold, tight tracking, tight line height)
    func heroTitle() -> some View {
        self
            .font(Typography.heroTitle)
            .tracking(Typography.trackingTight)
            .lineSpacing((48 * Typography.lineHeightTight) - 48)
    }

    /// Apply page title styling (28pt semibold, tight tracking)
    func pageTitle() -> some View {
        self
            .font(Typography.pageTitle)
            .tracking(Typography.trackingTight)
            .lineSpacing((28 * Typography.lineHeightTight) - 28)
    }

    /// Apply section title styling (20pt semibold)
    func sectionTitle() -> some View {
        self
            .font(Typography.sectionTitle)
            .tracking(Typography.trackingNormal)
    }

    /// Apply body text styling (14pt regular, normal line height)
    func bodyText() -> some View {
        self
            .font(Typography.bodyText)
            .tracking(Typography.trackingNormal)
            .lineSpacing((14 * Typography.lineHeightNormal) - 14)
    }

    /// Apply caption text styling (12pt regular, wide tracking)
    func captionText() -> some View {
        self
            .font(Typography.captionText)
            .tracking(Typography.trackingWide)
    }

    /// Apply monospace text styling (14pt monospaced)
    func monospaceText() -> some View {
        self
            .font(Typography.monospaceText)
            .tracking(Typography.trackingNormal)
            .lineSpacing((14 * Typography.lineHeightNormal) - 14)
    }
}
