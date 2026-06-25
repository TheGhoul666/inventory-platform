// swift-tools-version: 5.10
import PackageDescription

let package = Package(
    name: "BusOpsInventory",
    platforms: [.iOS(.v16)],
    products: [
        .library(name: "BusOpsInventory", targets: ["BusOpsInventory"]),
    ],
    dependencies: [
        .package(url: "https://github.com/supabase/supabase-swift.git", from: "2.0.0"),
    ],
    targets: [
        .target(
            name: "BusOpsInventory",
            dependencies: [
                .product(name: "Supabase", package: "supabase-swift"),
                .product(name: "Realtime", package: "supabase-swift"),
                .product(name: "PostgREST", package: "supabase-swift"),
                .product(name: "Auth", package: "supabase-swift"),
            ]
        ),
    ]
)
