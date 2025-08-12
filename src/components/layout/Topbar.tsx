import { Bell, ChevronDown, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const Topbar = () => {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="h-16 flex items-center gap-3 px-4">
        <div className="relative hidden md:flex items-center w-96">
          <Search className="absolute left-3 h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <Input className="pl-9" placeholder="Search jobs, courses..." aria-label="Global search" />
        </div>
        <div className="ml-auto flex items-center gap-3">
          <button className="relative inline-flex items-center justify-center rounded-md px-3 py-2 text-sm hover:bg-accent focus-ring" aria-label="Notifications">
            <Bell className="h-4 w-4" />
          </button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm hover:bg-accent focus-ring" aria-haspopup="menu" aria-label="Current college">
                <span className="text-sm">Your College</span>
                <ChevronDown className="h-4 w-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="dropdown-panel w-56">
              <DropdownMenuLabel>Select context</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>ABC Institute</DropdownMenuItem>
              <DropdownMenuItem>XYZ University</DropdownMenuItem>
              <DropdownMenuItem>Global College</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <div className="inline-flex items-center gap-2">
            <Avatar>
              <AvatarFallback aria-label="User">SC</AvatarFallback>
            </Avatar>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
