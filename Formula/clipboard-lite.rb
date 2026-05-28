class ClipboardLite < Formula
  desc "Lightweight Clipboard History Manager with CLI and GUI"
  homepage "https://github.com/codemaster-ar/homebrew-clipboard-lite"
  url "https://github.com/Codemaster-AR/homebrew-clipboard-lite/archive/refs/tags/v2.0.0.tar.gz"
  sha256 "17ddb8f6a27d05434f882c176a5c07321f81bf02f96d9dc1e2d2df33759b86dc"
  version "2.0.0"
  license "ISC"

  depends_on "node"
  depends_on "python@3.11"

  def install
    # 1. Install Node dependencies
    # We use --production to skip devDependencies
    system "npm", "install", "--production"

    # 2. Setup the application in libexec (private storage)
    # This keeps the binary directory clean
    libexec.install Dir["*"]

    # 3. Create a wrapper script to run the Python CLI
    # This ensures it uses the correct Python and environment
    (bin/"clipboard-lite").write <<~EOS
      #!/bin/bash
      # Add homebrew node/python to PATH just in case
      export PATH="#{HOMEBREW_PREFIX}/bin:$PATH"
      
      # Run the python script from the installed libexec directory
      # We assume dependencies like 'pyperclip' are available in the system python 
      # or should be installed via 'pip' by the user.
      exec python3 "#{libexec}/script.py" "$@"
    EOS
    
    chmod 0755, bin/"clipboard-lite"
  end

  def caveats
    <<~EOS
      To use the CLI, simply run:
        clipboard-lite

      To launch the GUI, select Option 2 from the CLI menu.
      
      Note: Ensure you have installed the required Python packages:
        pip3 install pyperclip rich pyfiglet
    EOS
  end

  test do
    # Basic test to ensure the binary is created and executable
    system "#{bin}/clipboard-lite", "--help"
  end
end
