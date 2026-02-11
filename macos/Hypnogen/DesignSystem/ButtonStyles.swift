import SwiftUI

// MARK: - Primary Button Style

/// Primary action button with accent background
struct PrimaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .semibold))
            .padding(.horizontal, Spacing.md)
            .padding(.vertical, Spacing.sm)
            .background(
                isEnabled 
                    ? (configuration.isPressed ? Color.accentPrimary.opacity(0.8) : Color.accentPrimary)
                    : Color.accentPrimary.opacity(0.4)
            )
            .foregroundColor(Color.canvas)
            .cornerRadius(Radius.sm)
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// MARK: - Secondary Button Style

/// Secondary action button with surface background and stroke
struct SecondaryButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .medium))
            .padding(.horizontal, Spacing.md)
            .padding(.vertical, Spacing.sm)
            .background(
                configuration.isPressed ? Color.surface.opacity(0.8) : Color.surface
            )
            .foregroundColor(isEnabled ? Color.textPrimary : Color.textSecondary)
            .overlay(
                RoundedRectangle(cornerRadius: Radius.sm)
                    .stroke(Color.stroke, lineWidth: 1)
            )
            .cornerRadius(Radius.sm)
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// MARK: - Ghost Button Style

/// Ghost button with no background, just text
struct GhostButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 14, weight: .medium))
            .padding(.horizontal, Spacing.sm)
            .padding(.vertical, Spacing.xs)
            .foregroundColor(
                isEnabled 
                    ? (configuration.isPressed ? Color.accentSecondary : Color.accentPrimary)
                    : Color.textSecondary
            )
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.1), value: configuration.isPressed)
    }
}

// MARK: - View Extensions

extension View {
    /// Apply primary button styling
    func primaryButtonStyle() -> some View {
        self.buttonStyle(PrimaryButtonStyle())
    }
    
    /// Apply secondary button styling
    func secondaryButtonStyle() -> some View {
        self.buttonStyle(SecondaryButtonStyle())
    }
    
    /// Apply ghost button styling
    func ghostButtonStyle() -> some View {
        self.buttonStyle(GhostButtonStyle())
    }
}
