export function Footer() {
  return (
    <footer className="w-full border-t border-gray-200 bg-gray-50 py-4 mt-auto">
      <div className="container mx-auto px-4 text-center text-sm text-gray-600">
        <p>
          Jason "Scott" Person |{" "}
          <a
            href="https://www.newmanu.edu"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 hover:underline"
          >
            Newman University
          </a>{" "}
          |{" "}
          <a
            href="https://github.com/jsperson/querydawg"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:text-blue-800 hover:underline"
          >
            GitHub
          </a>
        </p>
      </div>
    </footer>
  );
}
