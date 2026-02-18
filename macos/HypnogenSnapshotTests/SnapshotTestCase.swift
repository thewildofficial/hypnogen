import XCTest
import SnapshotTesting
import SwiftUI

/// Base class for Hypnogen snapshot tests. Subclass to test individual views.
/// Config: 0.99 perceptual precision, 1100x700 default size, dark mode primary.
class SnapshotTestCase: XCTestCase {

    // MARK: - Configuration

    static let defaultWindowSize = CGSize(width: 1100, height: 700)

    /// 0.99 tolerates anti-aliasing/font hinting while catching real regressions.
    static let perceptualPrecision: Float = 0.99

    /// Override to `true` to record new baseline snapshots.
    var isRecording: Bool { false }

    // MARK: - Helpers

    func assertDarkModeSnapshot<V: View>(
        of view: V,
        size: CGSize = SnapshotTestCase.defaultWindowSize,
        precision: Float = 1.0,
        perceptualPrecision: Float = SnapshotTestCase.perceptualPrecision,
        named name: String? = nil,
        file: StaticString = #file,
        testName: String = #function,
        line: UInt = #line
    ) {
        let hosted = NSHostingController(rootView:
            view
                .frame(width: size.width, height: size.height)
                .preferredColorScheme(.dark)
        )
        hosted.view.frame = CGRect(origin: .zero, size: size)

        assertSnapshot(
            of: hosted,
            as: .image(precision: precision, perceptualPrecision: perceptualPrecision, size: size),
            named: name,
            record: isRecording,
            file: file,
            testName: testName,
            line: line
        )
    }

    /// Snapshots in both dark and light mode with ".dark" / ".light" suffixes.
    func assertBothModesSnapshot<V: View>(
        of view: V,
        size: CGSize = SnapshotTestCase.defaultWindowSize,
        precision: Float = 1.0,
        perceptualPrecision: Float = SnapshotTestCase.perceptualPrecision,
        file: StaticString = #file,
        testName: String = #function,
        line: UInt = #line
    ) {
        let darkHosted = NSHostingController(rootView:
            view
                .frame(width: size.width, height: size.height)
                .preferredColorScheme(.dark)
        )
        darkHosted.view.frame = CGRect(origin: .zero, size: size)

        assertSnapshot(
            of: darkHosted,
            as: .image(precision: precision, perceptualPrecision: perceptualPrecision, size: size),
            named: "dark",
            record: isRecording,
            file: file,
            testName: testName,
            line: line
        )

        let lightHosted = NSHostingController(rootView:
            view
                .frame(width: size.width, height: size.height)
                .preferredColorScheme(.light)
        )
        lightHosted.view.frame = CGRect(origin: .zero, size: size)

        assertSnapshot(
            of: lightHosted,
            as: .image(precision: precision, perceptualPrecision: perceptualPrecision, size: size),
            named: "light",
            record: isRecording,
            file: file,
            testName: testName,
            line: line
        )
    }
}
