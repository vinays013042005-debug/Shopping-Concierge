"""
Script to generate high-resolution PNG diagrams for System Architecture and User Flow.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def draw_system_architecture(output_path):
    fig, ax = plt.subplots(figsize=(14, 10), dpi=300)
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#F8F9FA')
    ax.axis('off')

    c_tier_bg = '#FFFFFF'
    c_border = '#CBD5E1'
    c_blue = '#1E3A8A'
    c_blue_bg = '#EFF6FF'
    c_purple = '#6B21A8'
    c_purple_bg = '#FAF5FF'
    c_green = '#15803D'
    c_green_bg = '#F0FDF4'
    c_amber = '#B45309'
    c_amber_bg = '#FFFBEB'
    c_text_dark = '#0F172A'
    c_text_muted = '#475569'

    # Title
    ax.text(7, 9.6, "System Architecture: Hyper-Personalized Retail Concierge", 
            fontsize=18, fontweight='bold', ha='center', color=c_text_dark, family='sans-serif')
    ax.text(7, 9.25, "Local E-Commerce RAG with Inventory Guardrails & Computer Vision", 
            fontsize=11, ha='center', color=c_text_muted, family='sans-serif')

    def draw_box(x, y, w, h, title, subtitle, bg_color, border_color, title_color=c_text_dark):
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15", 
                                     facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 0.28, title, fontsize=10, fontweight='bold', ha='center', va='top', color=title_color)
        if subtitle:
            ax.text(x + w/2, y + 0.22, subtitle, fontsize=8, ha='center', va='bottom', color=c_text_muted)

    def draw_layer_bg(x, y, w, h, label):
        layer_box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.2", 
                                          facecolor=c_tier_bg, edgecolor=c_border, linewidth=1.2, linestyle='--')
        ax.add_patch(layer_box)
        ax.text(x + 0.3, y + h - 0.35, label, fontsize=11, fontweight='bold', color=c_blue, va='top')

    # Layer 1: Frontend Layer
    draw_layer_bg(0.8, 7.2, 12.4, 1.7, "Layer 1: Presentation Layer (Client Browser)")
    draw_box(1.2, 7.45, 2.7, 0.95, "Stylist Chatbot", "Conversational UI & Prompts", c_blue_bg, c_blue)
    draw_box(4.2, 7.45, 2.7, 0.95, "Photo Size Assistant", "Upload & Landmark Canvas", c_purple_bg, c_purple)
    draw_box(7.2, 7.45, 2.7, 0.95, "Live Inventory Store", "Interactive Catalog Cards", c_green_bg, c_green)
    draw_box(10.1, 7.45, 2.7, 0.95, "Customer Profile", "Style & Sizing Preferences", c_amber_bg, c_amber)

    # Layer 2: API Gateway Layer
    draw_layer_bg(0.8, 5.2, 12.4, 1.5, "Layer 2: API Gateway (FastAPI Backend)")
    draw_box(1.2, 5.45, 2.7, 0.85, "POST /api/chat", "Intent & Recommendations", '#F1F5F9', c_border)
    draw_box(4.2, 5.45, 2.7, 0.85, "POST /api/size-assistant", "Landmarks & Calibration", '#F1F5F9', c_border)
    draw_box(7.2, 5.45, 2.7, 0.85, "GET /api/products", "Filtered In-Stock Items", '#F1F5F9', c_border)
    draw_box(10.1, 5.45, 2.7, 0.85, "GET /api/customers", "Personalization Profiles", '#F1F5F9', c_border)

    # Layer 3: AI & Business Logic Layer
    draw_layer_bg(0.8, 2.7, 12.4, 2.0, "Layer 3: AI Engine & Guardrail Verification Services")
    draw_box(1.2, 2.95, 2.7, 1.25, "Ollama / NLP Engine", "Qwen 2.5 3B / Fallback\nIntent Extraction & Explanation", c_blue_bg, c_blue)
    draw_box(4.2, 2.95, 2.7, 1.25, "RAG Vector Retrieval", "SentenceTransformers\nall-MiniLM-L6-v2 (384-dim)", c_purple_bg, c_purple)
    draw_box(7.2, 2.95, 2.7, 1.25, "Inventory Guardrail", "Live Stock & Budget Cap\nSuppresses Out-of-Stock Sizes", c_green_bg, c_green)
    draw_box(10.1, 2.95, 2.7, 1.25, "Vision Sizing Engine", "MediaPipe Pose + OpenCV\nEllipse Anthropometric Model", c_amber_bg, c_amber)

    # Layer 4: Storage Layer
    draw_layer_bg(0.8, 0.6, 12.4, 1.6, "Layer 4: Local Storage (Zero Cloud Dependence)")
    draw_box(1.5, 0.85, 4.5, 0.95, "ChromaDB Vector Store", "Dense Semantic Embeddings Index (HNSW)", c_purple_bg, c_purple)
    draw_box(7.0, 0.85, 5.8, 0.95, "SQLite Relational Database (Source of Truth)", "products, variants, inventory, customers, size_charts", c_green_bg, c_green)

    def draw_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color='#64748B', lw=1.6, mutation_scale=12))
        if label:
            ax.text((x1 + x2)/2, (y1 + y2)/2, label, fontsize=7.5, ha='center', va='center', 
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=0.8), color=c_text_dark)

    draw_arrow(2.55, 7.45, 2.55, 6.30)
    draw_arrow(5.55, 7.45, 5.55, 6.30)
    draw_arrow(8.55, 7.45, 8.55, 6.30)
    draw_arrow(11.45, 7.45, 11.45, 6.30)

    draw_arrow(2.55, 5.45, 2.55, 4.20)
    draw_arrow(5.55, 5.45, 11.45, 4.20)
    draw_arrow(2.55, 4.20, 5.55, 4.20, "Semantic Query")
    draw_arrow(5.55, 4.20, 8.55, 4.20, "Candidates")

    draw_arrow(5.55, 2.95, 3.75, 1.80)
    draw_arrow(8.55, 2.95, 9.9, 1.80, "Real-time Verification")
    draw_arrow(11.45, 2.95, 9.9, 1.80, "Size Chart Lookup")

    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10.2)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(output_path), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved System Architecture diagram to:", str(output_path))

def draw_user_flow(output_path):
    fig, ax = plt.subplots(figsize=(14, 11), dpi=300)
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#F8F9FA')
    ax.axis('off')

    c_blue = '#1E3A8A'
    c_blue_bg = '#EFF6FF'
    c_purple = '#6B21A8'
    c_purple_bg = '#FAF5FF'
    c_green = '#15803D'
    c_green_bg = '#F0FDF4'
    c_amber = '#B45309'
    c_amber_bg = '#FFFBEB'
    c_rose = '#BE123C'
    c_rose_bg = '#FFF1F2'
    c_text_dark = '#0F172A'
    c_text_muted = '#475569'
    c_border = '#CBD5E1'

    # Title
    ax.text(7, 10.6, "User Flow: Shopping Concierge & Photo Sizing", 
            fontsize=18, fontweight='bold', ha='center', color=c_text_dark, family='sans-serif')
    ax.text(7, 10.25, "Step-by-step path from customer request to verified recommendation", 
            fontsize=11, ha='center', color=c_text_muted, family='sans-serif')

    def draw_node(x, y, w, h, title, subtitle="", bg_color='#FFFFFF', border_color=c_border, is_decision=False):
        if is_decision:
            poly = patches.Polygon([
                [x + w/2, y + h],
                [x + w, y + h/2],
                [x + w/2, y],
                [x, y + h/2]
            ], closed=True, facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
            ax.add_patch(poly)
            ax.text(x + w/2, y + h/2, title, fontsize=9.5, fontweight='bold', ha='center', va='center', color=c_text_dark)
        else:
            box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.15", 
                                         facecolor=bg_color, edgecolor=border_color, linewidth=1.5)
            ax.add_patch(box)
            if subtitle:
                ax.text(x + w/2, y + h - 0.22, title, fontsize=10, fontweight='bold', ha='center', va='top', color=c_text_dark)
                ax.text(x + w/2, y + 0.18, subtitle, fontsize=8, ha='center', va='bottom', color=c_text_muted)
            else:
                ax.text(x + w/2, y + h/2, title, fontsize=10, fontweight='bold', ha='center', va='center', color=c_text_dark)

    def draw_flow_arrow(x1, y1, x2, y2, label=""):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color='#475569', lw=1.6, mutation_scale=12))
        if label:
            ax.text((x1 + x2)/2, (y1 + y2)/2 + 0.12, label, fontsize=8, fontweight='bold', ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.15", facecolor='#FFFFFF', edgecolor='#CBD5E1', lw=0.6), color=c_text_dark)

    # Start Node
    draw_node(5.2, 9.3, 3.6, 0.7, "1. Shopper Enters Web App", "Selects Chat Stylist or Photo Sizing", c_blue_bg, c_blue)

    # Chat Flow (Left)
    draw_node(1.0, 7.8, 5.0, 0.9, "2A. Natural Language Query", "e.g. 'Beach wedding outfit under ₹3,000 in pastel linen'", c_blue_bg, c_blue)
    draw_node(1.0, 6.3, 5.0, 0.9, "3A. AI Intent Extraction", "Extracts: Occasion, Budget, Category, Fit, Color, Fabric", c_blue_bg, c_blue)
    draw_node(1.0, 4.8, 5.0, 0.9, "4A. Semantic Vector Search", "ChromaDB dense search retrieves candidate products", c_purple_bg, c_purple)

    # Guardrail Decision
    draw_node(1.2, 2.9, 4.6, 1.3, "5A. In Stock in SQLite\n& <= Budget Cap?", "", c_amber_bg, c_amber, is_decision=True)

    draw_node(0.5, 1.2, 3.2, 0.9, "6A. Verified In-Stock", "Personalization score boost\napplied to ranking", c_green_bg, c_green)
    draw_node(4.2, 1.2, 3.2, 0.9, "6B. Guardrail Fallback", "Filters out sold-out items\n& suggests in-stock alts", c_rose_bg, c_rose)

    # Photo Sizing Flow (Right)
    draw_node(8.0, 7.8, 5.0, 0.9, "2B. Photo Upload & Consent", "Explicit consent check + front-facing full-body photo", c_purple_bg, c_purple)
    draw_node(8.0, 6.3, 5.0, 0.9, "3B. MediaPipe Landmark Detection", "Detects shoulders, torso, hips, and total pixel height", c_purple_bg, c_purple)
    draw_node(8.0, 4.8, 5.0, 0.9, "4B. Anthropometric Calibration", "Optional user height scales cm/px via ellipse model", c_amber_bg, c_amber)
    draw_node(8.0, 3.3, 5.0, 0.9, "5B. Brand Size Chart Lookup", "Matches estimated chest/waist to Linen Trail/Aura charts", c_amber_bg, c_amber)
    draw_node(8.0, 1.8, 5.0, 0.9, "6C. Recommended Size Badge", "Shows Size M + Confidence Gauge (Uncalibrated/High)", c_green_bg, c_green)

    # Final Node
    draw_node(3.0, 0.1, 8.0, 0.7, "7. Stylist Response & Interactive Product Cards Displayed", "Grounded explanations, live stock pills, verified size selector, and match rationale", c_blue_bg, c_blue)

    # Connections
    draw_flow_arrow(7.0, 9.3, 3.5, 8.7, "Stylist Path")
    draw_flow_arrow(7.0, 9.3, 10.5, 8.7, "Sizing Path")

    draw_flow_arrow(3.5, 7.8, 3.5, 7.2)
    draw_flow_arrow(3.5, 6.3, 3.5, 5.7)
    draw_flow_arrow(3.5, 4.8, 3.5, 4.2)

    draw_flow_arrow(2.0, 2.9, 2.0, 2.1, "YES (Pass)")
    draw_flow_arrow(5.0, 2.9, 5.0, 2.1, "NO (Fail)")

    draw_flow_arrow(2.1, 1.2, 5.5, 0.8)
    draw_flow_arrow(5.8, 1.2, 6.5, 0.8)

    draw_flow_arrow(10.5, 7.8, 10.5, 7.2)
    draw_flow_arrow(10.5, 6.3, 10.5, 5.7)
    draw_flow_arrow(10.5, 4.8, 10.5, 4.2)
    draw_flow_arrow(10.5, 3.3, 10.5, 2.7)
    draw_flow_arrow(8.0, 2.25, 6.0, 7.8, "One-Click: Use in Chat")
    draw_flow_arrow(10.5, 1.8, 8.5, 0.8)

    ax.set_xlim(0, 14)
    ax.set_ylim(11.2)
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(str(output_path), format='png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved User Flow diagram to:", str(output_path))

if __name__ == "__main__":
    p1 = BASE_DIR / "system_architecture.png"
    p2 = BASE_DIR / "user_flow.png"
    draw_system_architecture(p1)
    draw_user_flow(p2)
