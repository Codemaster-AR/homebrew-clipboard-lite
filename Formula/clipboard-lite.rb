class ClipboardLite < Formula
  desc "Lightweight Clipboard History Manager with CLI and GUI"
  homepage "https://github.com/codemaster-ar/homebrew-clipboard-lite"
  url "https://github.com/Codemaster-AR/homebrew-clipboard-lite/archive/refs/tags/v2.0.0.tar.gz"
  sha256 "31a237a19375622828dff2732e747471d8a313313f6e2cb933b440bc259e1113"
  version "2.0.0"
  license "ISC"

  depends_on "node"
  depends_on "python@3.11"

  def install
    # Run npm install BEFORE moving files — package.json must exist in tarball root
    # Uses Homebrew's own node to avoid system version mismatches
    system "#{Formula["node"].opt_bin}/npm", "install", "--omit=dev"

    # Move everything (including node_modules) into libexec
    libexec.install Dir["*"]

    # Cross-platform wrapper: ensures both node and python resolve to
    # Homebrew-managed versions, and that Python subprocesses inherit PATH
    # so the GUI (node) can be launched by script.py on any OS
    (bin/"clipboard-lite").write <<~EOS
      #!/usr/bin/env bash
      export PATH="#{Formula["node"].opt_bin}:#{Formula["python@3.11"].opt_bin}:$PATH"
      export CLIPBOARD_LITE_DIR="#{libexec}"
      exec "#{Formula["python@3.11"].opt_bin}/python3" "#{libexec}/script.py" "$@"
    EOS

    chmod 0755, bin/"clipboard-lite"
  end

  def caveats
    <<~EOS
      To use the CLI, run:
        clipboard-lite

      The GUI option is available from the CLI menu (Option 2).

      If you see Python import errors, install the required packages:
        pip3 install pyperclip rich pyfiglet
    EOS
  end

  test do
    system bin/"clipboard-lite", "--help"
  end
end
